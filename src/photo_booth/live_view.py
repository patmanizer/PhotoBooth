"""Live view and gesture-triggered capture."""

import math
import random
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import gphoto2 as gp
import mediapipe as mp
import numpy as np
import qrcode

from .capture import (
    capture_photo,
    next_main_foreground_path,
    process_captured_photos,
    save_capture_output,
)
from .config import (
    COUNTDOWN_SECONDS,
    DROPBOX_QR_DISPLAY_SECONDS,
    GESTURE_HOLD_TIME,
    PHOTO_PROMPTS,
    PROCESSING_PROMPTS,
    PROMPT_DISPLAY_SECONDS,
)
from .drawing import (
    _draw_centered_text,
    draw_capture_countdown,
    draw_gesture_progress,
    draw_processing_message,
    draw_steady_message,
    crop_frame_to_portrait,
)
from .foregrounds import (
    ForegroundCycler,
    load_foreground,
    overlay_foreground,
)
from .gestures import get_raised_finger_count
from .hand_detector import create_hand_detector
from .logging_utils import log

_LIVE_VIEW_WINDOW = "Live View"
_DISPLAY_SCALE = 3


def _upscale_display_frame(frame, interpolation=cv2.INTER_CUBIC):
    """Scale a composed frame for display without changing its layout."""
    return cv2.resize(
        frame,
        None,
        fx=_DISPLAY_SCALE,
        fy=_DISPLAY_SCALE,
        interpolation=interpolation,
    )


def _create_dropbox_display_frame(photo_path, shared_url, frame_shape, scale=1):
    photo = cv2.imread(str(photo_path))
    if photo is None:
        raise RuntimeError(f"Could not load output photo for QR display: {photo_path}")

    qr_image = qrcode.make(shared_url).convert("RGB")
    qr = cv2.cvtColor(np.asarray(qr_image), cv2.COLOR_RGB2BGR)

    height, width = frame_shape[:2]
    height *= scale
    width *= scale
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    margin = max(16, min(height, width) // 30)
    photo_area_width = int(width * 0.62) - 2 * margin
    photo_area_height = height - 2 * margin
    photo_scale = min(
        photo_area_width / photo.shape[1],
        photo_area_height / photo.shape[0],
    )
    photo_size = (
        max(1, round(photo.shape[1] * photo_scale)),
        max(1, round(photo.shape[0] * photo_scale)),
    )
    photo = cv2.resize(photo, photo_size, interpolation=cv2.INTER_AREA)
    photo_x = margin + (photo_area_width - photo.shape[1]) // 2
    photo_y = margin + (photo_area_height - photo.shape[0]) // 2
    canvas[
        photo_y : photo_y + photo.shape[0],
        photo_x : photo_x + photo.shape[1],
    ] = photo

    qr_size = min(int(width * 0.30), int(height * 0.50))
    qr = cv2.resize(qr, (qr_size, qr_size), interpolation=cv2.INTER_NEAREST)
    qr_x = int(width * 0.66) + (int(width * 0.30) - qr_size) // 2
    qr_y = max(margin, (height - qr_size) // 2)
    canvas[qr_y : qr_y + qr_size, qr_x : qr_x + qr_size] = qr

    _draw_centered_text(
        canvas,
        "SCAN TO VIEW PHOTO",
        (
            int(width * 0.66) + int(width * 0.15),
            max(margin // 2, qr_y - margin),
        ),
        max(24, int(min(height, width) * 0.06)),
        (255, 255, 255),
        max_width=int(width * 0.30),
    )
    return canvas


def _process_captured_photo(captured_photo):
    """Process one capture off the UI thread while the burst continues."""
    processed_images = process_captured_photos((captured_photo,))
    return processed_images[0]


def _save_capture_batch(processing_futures, main_foreground_path):
    """Create the final output after all individually queued photos finish."""
    processed_images = []
    processing_errors = []
    for processing_future in processing_futures:
        try:
            processed_images.append(processing_future.result())
        except Exception as exc:
            processing_errors.append(exc)

    if processing_errors:
        raise RuntimeError(
            f"Failed to process {len(processing_errors)} captured photo(s)"
        ) from processing_errors[0]

    return save_capture_output(processed_images, main_foreground_path)


def stream_live_view():
    """Run live view until the user presses Q."""

    camera = gp.Camera()
    initialized = False
    hand_detector = None
    image_executor = ThreadPoolExecutor(max_workers=1)
    foreground_cycler = ForegroundCycler()
    cached_foreground = None
    cached_frame_size = None
    cached_foreground_display_path = None
    live_view_window_open = False

    try:
        # --------------------------------------------------
        # Initialize camera.
        # --------------------------------------------------
        camera.init()
        initialized = True

        log("Nikon D7000 initialized.")

        # --------------------------------------------------
        # Initialize MediaPipe.
        # --------------------------------------------------
        log("Starting MediaPipe hand detector...")

        hand_detector = create_hand_detector()

        log("MediaPipe ready.")

        # --------------------------------------------------
        # Gesture state.
        # --------------------------------------------------
        gesture_start = None
        gesture_finger_count = None
        gesture_capture_count = None

        live_view_active = True
        frame_timestamp_ms = 0
        pending_capture_count = None
        # Keep the original burst size while the remaining count decreases,
        # so every preview frame in a portrait burst stays portrait-cropped.
        capture_sequence_count = None
        capture_main_foreground_path = None
        capture_prompt = None
        countdown_started_at = None
        processing_futures = []
        # Process each photo in the worker while the burst continues.
        processing_future = None
        processing_prompt = None
        dropbox_display_frame = None
        dropbox_display_rendered_frame = None
        dropbox_display_countdown = None
        dropbox_display_until = None

        # --------------------------------------------------
        # Live-view loop.
        # --------------------------------------------------
        while True:
            if dropbox_display_until is not None:
                seconds_remaining = max(
                    0,
                    math.ceil(dropbox_display_until - time.monotonic()),
                )
                if seconds_remaining != dropbox_display_countdown:
                    dropbox_display_rendered_frame = dropbox_display_frame.copy()
                    _draw_centered_text(
                        dropbox_display_rendered_frame,
                        f"RETURNING IN {seconds_remaining}s",
                        (
                            int(dropbox_display_frame.shape[1] * 0.81),
                            int(dropbox_display_frame.shape[0] * 0.90),
                        ),
                        max(
                            24,
                            int(min(dropbox_display_frame.shape[:2]) * 0.06),
                        ),
                        (255, 255, 255),
                        max_width=int(dropbox_display_frame.shape[1] * 0.30),
                    )
                    dropbox_display_countdown = seconds_remaining

                cv2.imshow(
                    _LIVE_VIEW_WINDOW,
                    dropbox_display_rendered_frame,
                )
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if time.monotonic() >= dropbox_display_until:
                    dropbox_display_frame = None
                    dropbox_display_rendered_frame = None
                    dropbox_display_countdown = None
                    dropbox_display_until = None
                else:
                    continue

            if live_view_active:

                # Get camera preview.
                camera_file = camera.capture_preview()

                file_data = camera_file.get_data_and_size()
                data_bytes = memoryview(file_data).tobytes()

                image_array = np.frombuffer(
                    data_bytes,
                    dtype=np.uint8,
                )

                frame = cv2.imdecode(
                    image_array,
                    cv2.IMREAD_COLOR,
                )

                if frame is None:
                    continue

                portrait_burst = capture_sequence_count in (2, 3)
                if portrait_burst:
                    # Keep preview and saved portrait captures framed alike.
                    frame = crop_frame_to_portrait(frame)

                display_frame = (
                    _upscale_display_frame(
                        frame,
                        interpolation=cv2.INTER_LANCZOS4,
                    )
                    if portrait_burst
                    else frame
                )

                foreground_display_path = None
                if capture_sequence_count == 1:
                    foreground_display_path = capture_main_foreground_path
                elif portrait_burst:
                    foreground_display_path = foreground_cycler.current_path

                if foreground_display_path is not None:
                    display_frame_size = (
                        display_frame.shape[1],
                        display_frame.shape[0],
                    )
                    if (
                        foreground_display_path != cached_foreground_display_path
                        or display_frame_size != cached_frame_size
                    ):
                        cached_foreground = load_foreground(
                            foreground_display_path,
                            display_frame_size,
                        )
                        cached_foreground_display_path = foreground_display_path
                        cached_frame_size = display_frame_size

                    overlay_foreground(display_frame, cached_foreground)

                # ------------------------------------------
                # MediaPipe hand detection.
                # ------------------------------------------
                detected_finger_count = None
                hand_landmarks = None
                if pending_capture_count is None:
                    rgb_frame = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGB,
                    )

                    mp_image = mp.Image(
                        image_format=mp.ImageFormat.SRGB,
                        data=rgb_frame,
                    )

                    frame_timestamp_ms += 33

                    results = hand_detector.detect_for_video(
                        mp_image,
                        frame_timestamp_ms,
                    )

                    # ------------------------------------------
                    # Process detected hand.
                    # ------------------------------------------
                    if results.hand_landmarks:

                        # This is the complete landmark list
                        # for the first detected hand.
                        hand_landmarks = results.hand_landmarks[0]

                        detected_finger_count = get_raised_finger_count(
                            hand_landmarks
                        )

                        draw_gesture_progress(
                            display_frame,
                            hand_landmarks,
                            0.0,
                            detected_finger_count,
                        )

                # ------------------------------------------
                # Gesture hold timer.
                # ------------------------------------------
                if (
                    detected_finger_count is not None
                    and gesture_capture_count is None
                    and pending_capture_count is None
                ):

                    if detected_finger_count != gesture_finger_count:
                        gesture_finger_count = detected_finger_count
                        gesture_start = time.time()

                    elapsed = time.time() - gesture_start

                    progress = min(
                        elapsed / GESTURE_HOLD_TIME,
                        1.0,
                    )

                    if hand_landmarks is not None:
                        draw_gesture_progress(
                            display_frame,
                            hand_landmarks,
                            progress,
                            detected_finger_count,
                        )

                    if elapsed >= GESTURE_HOLD_TIME:

                        log(
                            f"{detected_finger_count}-finger gesture "
                            "triggered!"
                        )

                        gesture_capture_count = detected_finger_count
                        gesture_start = None

                else:

                    gesture_start = None
                    gesture_finger_count = None

                if pending_capture_count is not None:
                    if countdown_started_at is None:
                        countdown_number = None
                    else:
                        elapsed = time.monotonic() - countdown_started_at
                        countdown_elapsed = elapsed - PROMPT_DISPLAY_SECONDS
                        if elapsed < PROMPT_DISPLAY_SECONDS:
                            countdown_number = None
                        else:
                            # Hold "1" until the capture threshold is reached.
                            countdown_number = max(
                                1,
                                COUNTDOWN_SECONDS - int(countdown_elapsed),
                            )
                    draw_capture_countdown(
                        display_frame,
                        capture_prompt,
                        countdown_number,
                        scale=_DISPLAY_SCALE if portrait_burst else 1,
                    )

                # ------------------------------------------
                # Display live view.
                # ------------------------------------------
                if not live_view_window_open:
                    cv2.namedWindow(_LIVE_VIEW_WINDOW, cv2.WINDOW_NORMAL)
                    cv2.setWindowProperty(
                        _LIVE_VIEW_WINDOW,
                        cv2.WND_PROP_FULLSCREEN,
                        cv2.WINDOW_FULLSCREEN,
                    )
                    live_view_window_open = True

                cv2.imshow(
                    _LIVE_VIEW_WINDOW,
                    display_frame
                    if portrait_burst
                    else _upscale_display_frame(display_frame),
                )
            elif processing_future is not None:
                processing_frame = np.zeros(
                    (
                        frame.shape[0] * _DISPLAY_SCALE,
                        frame.shape[1] * _DISPLAY_SCALE,
                        frame.shape[2],
                    ),
                    dtype=frame.dtype,
                )
                draw_processing_message(
                    processing_frame,
                    processing_prompt,
                    scale=_DISPLAY_SCALE,
                )
                cv2.imshow(
                    _LIVE_VIEW_WINDOW,
                    processing_frame,
                )

            # --------------------------------------------------
            # Keyboard controls.
            # --------------------------------------------------
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if processing_future is not None and processing_future.done():
                # Surface worker errors on the UI thread before resuming capture.
                try:
                    output = processing_future.result()
                    if output is not None:
                        output_path, shared_url = output
                        if shared_url:
                            dropbox_display_frame = _create_dropbox_display_frame(
                                output_path,
                                shared_url,
                                frame.shape,
                                scale=_DISPLAY_SCALE,
                            )
                            dropbox_display_rendered_frame = None
                            dropbox_display_countdown = None
                            dropbox_display_until = (
                                time.monotonic() + DROPBOX_QR_DISPLAY_SECONDS
                            )
                except Exception as exc:
                    log(f"Photo output error: {exc}")
                processing_future = None
                processing_prompt = None
                live_view_active = True
                continue

            if (
                live_view_active
                and pending_capture_count is not None
                and countdown_started_at is None
            ):
                # Start timing only after the prompt has appeared in the window.
                countdown_started_at = time.monotonic()

            # Spacebar captures once; gestures capture once per raised finger.
            if pending_capture_count is None and (
                key == ord(" ") or gesture_capture_count is not None
            ):
                # Freeze the burst size and select its first prompt.
                pending_capture_count = gesture_capture_count or 1
                capture_sequence_count = pending_capture_count
                capture_main_foreground_path = next_main_foreground_path()
                capture_prompt = random.choice(PHOTO_PROMPTS)
                countdown_started_at = None

                gesture_capture_count = None
                gesture_start = None
                gesture_finger_count = None

            elif (
                pending_capture_count is not None
                and countdown_started_at is not None
                and time.monotonic() - countdown_started_at
                >= PROMPT_DISPLAY_SECONDS + COUNTDOWN_SECONDS
            ):
                # Stop live view.
                live_view_active = False

                steady_frame = np.zeros(
                    (
                        frame.shape[0] * _DISPLAY_SCALE,
                        frame.shape[1] * _DISPLAY_SCALE,
                        frame.shape[2],
                    ),
                    dtype=frame.dtype,
                )
                draw_steady_message(steady_frame, scale=_DISPLAY_SCALE)
                cv2.imshow(
                    _LIVE_VIEW_WINDOW,
                    steady_frame,
                )
                cv2.waitKey(1)

                time.sleep(0.2)

                foreground_path = foreground_cycler.current_path
                # Hold downloaded image data until the final shot is captured.
                captured_photo = capture_photo(
                    camera,
                    foreground_path,
                    crop_to_portrait=capture_sequence_count in (2, 3),
                    apply_individual_foreground=capture_sequence_count > 1,
                )
                if captured_photo is not None:
                    processing_futures.append(
                        image_executor.submit(
                            _process_captured_photo,
                            captured_photo,
                        )
                    )
                    foreground_cycler.advance()

                pending_capture_count -= 1
                if pending_capture_count:
                    # Resume live view for the next shot in a burst.
                    log("Resuming live view...")
                    time.sleep(0.5)
                    live_view_active = True
                    # Each burst photo gets a new prompt and a fresh countdown.
                    capture_prompt = random.choice(PHOTO_PROMPTS)
                    countdown_started_at = None
                else:
                    # The single worker processes these in capture order; queue
                    # final output creation behind the per-photo processing.
                    processing_future = image_executor.submit(
                        _save_capture_batch,
                        tuple(processing_futures),
                        capture_main_foreground_path,
                    )
                    processing_prompt = random.choice(PROCESSING_PROMPTS)
                    processing_futures = []
                    capture_sequence_count = None
                    capture_main_foreground_path = None
                    pending_capture_count = None

    except Exception as exc:
        log(f"Error: {exc}")
        raise

    finally:
        cv2.destroyAllWindows()

        if hand_detector:
            hand_detector.close()

        if initialized:
            camera.exit()

        image_executor.shutdown(wait=True)

        log("Camera closed.")