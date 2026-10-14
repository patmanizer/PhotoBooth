"""Live view and gesture-triggered capture."""

import random
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import gphoto2 as gp
import mediapipe as mp
import numpy as np

from .capture import (
    capture_photo,
    next_main_foreground_path,
    save_capture_output,
)
from .config import (
    COUNTDOWN_SECONDS,
    GESTURE_HOLD_TIME,
    PHOTO_PROMPTS,
    PROMPT_DISPLAY_SECONDS,
)
from .drawing import (
    draw_capture_countdown,
    draw_gesture_progress,
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

_LIVE_VIEW_WINDOW = "Live View"


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

        print("Nikon D7000 initialized.")

        # --------------------------------------------------
        # Initialize MediaPipe.
        # --------------------------------------------------
        print("Starting MediaPipe hand detector...")

        hand_detector = create_hand_detector()

        print("MediaPipe ready.")

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
        capture_image_futures = []

        # --------------------------------------------------
        # Live-view loop.
        # --------------------------------------------------
        while True:

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

                if capture_sequence_count in (2, 3):
                    # Keep preview and saved portrait captures framed alike.
                    frame = crop_frame_to_portrait(frame)

                foreground_display_path = None
                if capture_sequence_count == 1:
                    foreground_display_path = capture_main_foreground_path
                elif capture_sequence_count in (2, 3):
                    foreground_display_path = foreground_cycler.current_path

                if foreground_display_path is not None:
                    frame_size = (frame.shape[1], frame.shape[0])
                    if (
                        foreground_display_path != cached_foreground_display_path
                        or frame_size != cached_frame_size
                    ):
                        cached_foreground = load_foreground(
                            foreground_display_path,
                            frame_size,
                        )
                        cached_foreground_display_path = foreground_display_path
                        cached_frame_size = frame_size

                    overlay_foreground(frame, cached_foreground)

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
                            frame,
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
                            frame,
                            hand_landmarks,
                            progress,
                            detected_finger_count,
                        )

                    if elapsed >= GESTURE_HOLD_TIME:

                        print(
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
                        frame,
                        capture_prompt,
                        countdown_number,
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
                    frame,
                )

            # --------------------------------------------------
            # Keyboard controls.
            # --------------------------------------------------
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

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

                steady_frame = np.zeros_like(frame)
                draw_steady_message(steady_frame)
                cv2.imshow(_LIVE_VIEW_WINDOW, steady_frame)
                cv2.waitKey(1)

                time.sleep(0.2)

                foreground_path = foreground_cycler.current_path
                # Keep each image-processing future for the final burst output.
                image_future = capture_photo(
                    camera,
                    image_executor,
                    foreground_path,
                    crop_to_portrait=capture_sequence_count in (2, 3),
                    apply_individual_foreground=capture_sequence_count > 1,
                )
                if image_future is not None:
                    capture_image_futures.append(image_future)
                    foreground_cycler.advance()

                # Resume live view.
                print("Resuming live view...")

                time.sleep(0.5)

                live_view_active = True
                pending_capture_count -= 1
                if pending_capture_count:
                    # Each burst photo gets a new prompt and a fresh countdown.
                    capture_prompt = random.choice(PHOTO_PROMPTS)
                    countdown_started_at = None
                else:
                    save_capture_output(
                        capture_image_futures,
                        image_executor,
                        capture_main_foreground_path,
                    )
                    capture_image_futures = []
                    capture_sequence_count = None
                    capture_main_foreground_path = None
                    pending_capture_count = None

    except Exception as exc:
        print(f"Error: {exc}")
        raise

    finally:
        cv2.destroyAllWindows()

        if hand_detector:
            hand_detector.close()

        if initialized:
            camera.exit()

        image_executor.shutdown(wait=True)

        print("Camera closed.")