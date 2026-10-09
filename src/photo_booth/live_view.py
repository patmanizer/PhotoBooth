"""Live view and gesture-triggered capture."""

import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import gphoto2 as gp
import mediapipe as mp
import numpy as np

from .capture import capture_photo
from .config import GESTURE_HOLD_TIME
from .drawing import draw_gesture_progress
from .gestures import is_one_finger_up
from .hand_detector import create_hand_detector


def stream_live_view():
    """Run live view until the user presses Q."""

    camera = gp.Camera()
    initialized = False
    hand_detector = None
    image_executor = ThreadPoolExecutor(max_workers=1)

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
        gesture_triggered = False

        live_view_active = True
        frame_timestamp_ms = 0

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

                # ------------------------------------------
                # MediaPipe hand detection.
                # ------------------------------------------
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

                gesture_detected = False
                hand_landmarks = None

                # ------------------------------------------
                # Process detected hand.
                # ------------------------------------------
                if results.hand_landmarks:

                    # This is the complete landmark list
                    # for the first detected hand.
                    hand_landmarks = results.hand_landmarks[0]

                    gesture_detected = is_one_finger_up(
                        hand_landmarks
                    )

                    draw_gesture_progress(
                        frame,
                        hand_landmarks,
                        0.0,
                    )

                # ------------------------------------------
                # Gesture hold timer.
                # ------------------------------------------
                if gesture_detected and not gesture_triggered:

                    if gesture_start is None:
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
                        )

                    if elapsed >= GESTURE_HOLD_TIME:

                        print("One-finger gesture triggered!")

                        gesture_triggered = True
                        gesture_start = None

                elif not gesture_detected:

                    gesture_start = None
                    gesture_triggered = False

                # ------------------------------------------
                # Display live view.
                # ------------------------------------------
                cv2.imshow(
                    "Live View",
                    frame,
                )

            # --------------------------------------------------
            # Keyboard controls.
            # --------------------------------------------------
            key = cv2.waitKey(1) & 0xFF

            # Spacebar or gesture triggers a capture.
            if key == ord(" ") or gesture_triggered:

                gesture_triggered = False
                gesture_start = None

                # Stop live view.
                live_view_active = False

                cv2.destroyWindow("Live View")

                time.sleep(0.2)

                # Capture photo.
                capture_photo(camera, image_executor)

                # Resume live view.
                print("Resuming live view...")

                time.sleep(0.5)

                live_view_active = True

            # Q exits the application.
            elif key == ord("q"):
                break

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