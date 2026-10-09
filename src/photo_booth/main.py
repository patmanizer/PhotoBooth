import io
import os
import time
from pathlib import Path

import cv2
import numpy as np
import gphoto2 as gp
import mediapipe as mp
import rawpy
from PIL import Image
from rembg import remove

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# =============================================================
# Configuration
# =============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = str(
    PROJECT_ROOT / "hand_landmarker.task"
)

CAPTURE_FOLDER = str(Path(__file__).resolve().parent / "captured_images")

GESTURE_HOLD_TIME = 2

MIN_HAND_DETECTION_CONFIDENCE = 0.6
MIN_HAND_PRESENCE_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6


def configure_camera(camera):
    """
    Configure the Nikon D7000 for photo booth photography.
    """

    try:
        print("Configuring camera...")

        context = gp.Context()

        # -----------------------------------------------------
        # Set ISO to 200
        # -----------------------------------------------------
        print("Setting ISO to 200")

        try:
            config = camera.get_config(context)
            capture_settings = config.get_child_by_name("imgsettings")
            iso_widget = capture_settings.get_child_by_name("iso")

            iso_widget.set_value("200")
            camera.set_config(config, context)

            time.sleep(0.3)

            # Verify ISO
            config = camera.get_config(context)
            capture_settings = config.get_child_by_name("imgsettings")
            iso_widget = capture_settings.get_child_by_name("iso")

            actual_iso = iso_widget.get_value()
            print(f"ISO reported by camera: {actual_iso}")

        except gp.GPhoto2Error as e:
            print(f"Could not set ISO: {e}")


        # -----------------------------------------------------
        # Aperture: f/8
        # -----------------------------------------------------

        config = camera.get_config(context)
        capture_settings = config.get_child_by_name("capturesettings")

        widget = capture_settings.get_child_by_name("f-number")
        print("Setting F-Number to f/8")
        widget.set_value("f/8")

        camera.set_config(config, context)

        # -----------------------------------------------------
        # Shutter speed: 1/160 sec
        # -----------------------------------------------------

        config = camera.get_config(context)
        capture_settings = config.get_child_by_name("capturesettings")

        widget = capture_settings.get_child_by_name("shutterspeed")
        print("Setting Shutter Speed to 0.0062s")
        widget.set_value("0.0062s")

        camera.set_config(config, context)

        # -----------------------------------------------------
        # Nikon flash mode: TTL
        # -----------------------------------------------------

        config = camera.get_config(context)
        capture_settings = config.get_child_by_name("capturesettings")

        widget = capture_settings.get_child_by_name("nikonflashmode")
        print("Nikon Flash Mode set to iTTL")
        widget.set_value("iTTL")

        camera.set_config(config, context)

        config = camera.get_config(context)
        capture_settings = config.get_child_by_name("capturesettings")
        print("Camera configuration:")
        for label, widget_name in (
            ("Exposure", "expprogram"),
            ("Aperture", "f-number"),
            ("Shutter", "shutterspeed"),
            ("Flash", "nikonflashmode")
        ):
            value = capture_settings.get_child_by_name(widget_name).get_value()
            print(f"  {label}: {value}")

    except gp.GPhoto2Error as e:

        print(
            f"Could not configure camera: {e}"
        )


# =============================================================
# Open-hand detection
# =============================================================

def is_open_hand(hand_landmarks):
    """
    Detect an open palm facing the camera and pointing upward.

    Works for both left and right hands.
    """

    WRIST = 0

    wrist = hand_landmarks[WRIST]

    def distance_3d(a, b):
        return (
            (a.x - b.x) ** 2
            + (a.y - b.y) ** 2
            + (a.z - b.z) ** 2
        ) ** 0.5

    # =========================================================
    # 1. All four fingers must be extended
    # =========================================================

    fingers = [
        (8, 6),    # Index
        (12, 10),  # Middle
        (16, 14),  # Ring
        (20, 18),  # Pinky
    ]

    extended_fingers = 0

    for tip_index, pip_index in fingers:

        tip = hand_landmarks[tip_index]
        pip = hand_landmarks[pip_index]

        tip_distance = distance_3d(tip, wrist)
        pip_distance = distance_3d(pip, wrist)

        if tip_distance > pip_distance * 1.10:
            extended_fingers += 1

    if extended_fingers < 4:
        return False

    # =========================================================
    # 2. Thumb must be extended
    # =========================================================

    thumb_tip = hand_landmarks[4]
    thumb_ip = hand_landmarks[3]

    if (
        distance_3d(thumb_tip, wrist)
        <=
        distance_3d(thumb_ip, wrist) * 1.05
    ):
        return False

    # =========================================================
    # 3. Palm must point upward
    # =========================================================

    middle_tip = hand_landmarks[12]

    vertical_distance = wrist.y - middle_tip.y
    horizontal_distance = abs(wrist.x - middle_tip.x)

    # Fingertips must be above wrist
    if vertical_distance <= 0:
        return False

    # Hand should be substantially vertical
    if vertical_distance < horizontal_distance * 1.2:
        return False

    # =========================================================
    # 4. Palm must face camera
    #
    # Use the magnitude of the palm normal instead of its sign.
    # This makes it work for BOTH hands.
    # =========================================================

    index_mcp = hand_landmarks[5]
    pinky_mcp = hand_landmarks[17]

    ax = index_mcp.x - wrist.x
    ay = index_mcp.y - wrist.y
    az = index_mcp.z - wrist.z

    bx = pinky_mcp.x - wrist.x
    by = pinky_mcp.y - wrist.y
    bz = pinky_mcp.z - wrist.z

    # Palm normal
    nx = ay * bz - az * by
    ny = az * bx - ax * bz
    nz = ax * by - ay * bx

    normal_length = (
        nx ** 2 +
        ny ** 2 +
        nz ** 2
    ) ** 0.5

    if normal_length == 0:
        return False

    # How strongly the palm normal points toward/away
    # from the camera.
    facing_ratio = abs(nz) / normal_length

    # Require palm to be reasonably front-facing.
    if facing_ratio < 0.35:
        return False

    return True

# =============================================================
# Draw hand landmarks
# =============================================================

def draw_hand(frame, hand_landmarks):

    height, width, _ = frame.shape

    # Hand connections
    connections = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),

        (0, 5),
        (5, 6),
        (6, 7),
        (7, 8),

        (5, 9),
        (9, 10),
        (10, 11),
        (11, 12),

        (9, 13),
        (13, 14),
        (14, 15),
        (15, 16),

        (13, 17),
        (17, 18),
        (18, 19),
        (19, 20),

        (0, 17),
    ]

    # ---------------------------------------------------------
    # Draw connections
    # ---------------------------------------------------------

    for start_index, end_index in connections:

        start = hand_landmarks[start_index]
        end = hand_landmarks[end_index]

        start_point = (
            int(start.x * width),
            int(start.y * height)
        )

        end_point = (
            int(end.x * width),
            int(end.y * height)
        )

        cv2.line(
            frame,
            start_point,
            end_point,
            (0, 255, 0),
            2
        )

    # ---------------------------------------------------------
    # Draw landmarks
    # ---------------------------------------------------------

    for landmark in hand_landmarks:

        point = (
            int(landmark.x * width),
            int(landmark.y * height)
        )

        cv2.circle(
            frame,
            point,
            4,
            (0, 255, 0),
            -1
        )

def draw_gesture_progress(frame, hand_landmarks, progress):
    height, width, _ = frame.shape
    palm_landmarks = [
        hand_landmarks[index]
        for index in (0, 5, 9, 13, 17)
    ]
    palm_points = [
        (int(landmark.x * width), int(landmark.y * height))
        for landmark in palm_landmarks
    ]

    center = (
        sum(point[0] for point in palm_points) // len(palm_points),
        sum(point[1] for point in palm_points) // len(palm_points),
    )
    radius = max(
        12,
        int(
            max(
                (
                    (point[0] - center[0]) ** 2
                    + (point[1] - center[1]) ** 2
                ) ** 0.5
                for point in palm_points
            )
            * 0.8
        ),
    )
    thickness = max(5, radius // 2)

    cv2.circle(
        frame,
        center,
        radius,
        (80, 80, 80),
        thickness,
        cv2.LINE_AA,
    )

    if int(360 * progress) > 0:

        cv2.ellipse(
            frame,
            center,
            (radius, radius),
            0,
            -90,
            -90 + int(360 * progress),
            (0, 255, 0),
            thickness,
            cv2.LINE_AA,
        )


def is_finger_up(hand_landmarks, finger_tip, finger_pip):
    """Check whether a finger is raised."""

    return (
        hand_landmarks[finger_tip].y
        < hand_landmarks[finger_pip].y
    )

def is_one_finger_up(hand_landmarks):
    """
    Detect one finger pointing upward.
    Adjusts for hands appearing at different distances from the camera.
    """

    landmarks = hand_landmarks

    # Index finger landmarks
    wrist = landmarks[0]
    index_tip = landmarks[8]
    index_pip = landmarks[6]
    index_mcp = landmarks[5]

    # Other fingers must be folded
    middle_up = is_finger_up(landmarks, 12, 10)
    ring_up = is_finger_up(landmarks, 16, 14)
    pinky_up = is_finger_up(landmarks, 20, 18)

    # Check that the index finger is extended
    finger_extended = (
        index_tip.y < index_pip.y
        and index_pip.y < index_mcp.y
    )

    # Calculate hand size using the wrist-to-middle-finger-base distance
    hand_size = (
        (landmarks[9].x - wrist.x) ** 2
        + (landmarks[9].y - wrist.y) ** 2
    ) ** 0.5

    if hand_size < 0.001:
        return False

    # Require sufficient extension relative to hand size
    finger_length = index_mcp.y - index_tip.y
    pointing_up = finger_length / hand_size > 0.8

    # Ensure the finger points mostly upward
    vertical_distance = abs(index_tip.y - index_mcp.y)
    horizontal_distance = abs(index_tip.x - index_mcp.x)

    pointing_vertical = (
        horizontal_distance < vertical_distance * 0.75
    )

    return (
        finger_extended
        and pointing_up
        and pointing_vertical
        and not middle_up
        and not ring_up
        and not pinky_up
    )

def is_two_fingers_up(hand_landmarks):
    """
    Detect whether the index and middle fingers are raised.
    """
    index_up = is_finger_up(hand_landmarks, 8, 6)
    middle_up = is_finger_up(hand_landmarks, 12, 10)

    return index_up and middle_up


def is_three_fingers_up(hand_landmarks):
    """
    Detect whether the index, middle, and ring fingers are raised.
    """
    index_up = is_finger_up(hand_landmarks, 8, 6)
    middle_up = is_finger_up(hand_landmarks, 12, 10)
    ring_up = is_finger_up(hand_landmarks, 16, 14)

    return index_up and middle_up and ring_up

# =============================================================
# Create MediaPipe hand detector
# =============================================================

def create_hand_detector():

    if not os.path.exists(MODEL_PATH):

        raise FileNotFoundError(
            f"Could not find MediaPipe model: "
            f"{MODEL_PATH}\n\n"
            f"Download it using:\n"
            f"wget -O hand_landmarker.task "
            f"https://storage.googleapis.com/"
            f"mediapipe-models/hand_landmarker/"
            f"hand_landmarker/float16/1/"
            f"hand_landmarker.task"
        )

    base_options = python.BaseOptions(
        model_asset_path=MODEL_PATH
    )

    options = vision.HandLandmarkerOptions(
        base_options=base_options,

        running_mode=vision.RunningMode.VIDEO,

        num_hands=1,

        min_hand_detection_confidence=(
            MIN_HAND_DETECTION_CONFIDENCE
        ),

        min_hand_presence_confidence=(
            MIN_HAND_PRESENCE_CONFIDENCE
        ),

        min_tracking_confidence=(
            MIN_TRACKING_CONFIDENCE
        )
    )

    detector = (
        vision.HandLandmarker
        .create_from_options(options)
    )

    return detector

def autofocus(camera, context):
    """
    Trigger autofocus on the Nikon D7000 using python-gphoto2.
    """
    try:
        print("Reading autofocus control...")

        # Retrieve the actual configuration widget.
        widget = camera.get_single_config("autofocusdrive", context)

        print(f"Autofocus widget: {widget.get_name()}")
        print(f"Widget type: {widget.get_type()}")
        print(f"Current value: {widget.get_value()}")

        # Trigger autofocus.
        widget.set_value(1)

        print("Sending autofocus command...")

        camera.set_single_config(
            "autofocusdrive",
            widget,
            context
        )

        print("Autofocus command accepted.")
        time.sleep(1.0)
        return True

    except gp.GPhoto2Error as e:
        print(f"gphoto2 autofocus error: {e}")
        return False

    except Exception as e:
        print(f"Unexpected autofocus error: {e}")
        return False

# =============================================================
# Capture photo
# =============================================================

def capture_photo(camera):

    context = gp.Context()

    os.makedirs(
        CAPTURE_FOLDER,
        exist_ok=True
    )

    try:

        # -----------------------------------------------------
        # Reset camera connection before autofocus
        # -----------------------------------------------------

        print("Reinitializing Nikon camera...")

        camera.exit()
        time.sleep(0.5)

        camera.init()
        time.sleep(0.5)

        configure_camera(camera)

        # -----------------------------------------------------
        # Autofocus
        # -----------------------------------------------------

        print("Autofocusing...")

        autofocus_success = autofocus(
            camera,
            context
        )

        if autofocus_success:
            print("Autofocus command sent successfully.")
        else:
            print(
                "Autofocus command failed. "
                "Continuing with capture..."
            )

        # Give the camera a brief moment before triggering the shutter.
        time.sleep(0.3)

        # -----------------------------------------------------
        # Capture actual photo
        # -----------------------------------------------------

        print("Capturing photo...")

        file_path = camera.capture(
            gp.GP_CAPTURE_IMAGE
        )

        print(
            f"Image captured: {file_path.name}"
        )

        # -----------------------------------------------------
        # Download the camera's full-resolution capture
        # -----------------------------------------------------

        camera_file = camera.file_get(
            file_path.folder,
            file_path.name,
            gp.GP_FILE_TYPE_NORMAL
        )

        image_data = memoryview(
            camera_file.get_data_and_size()
        ).tobytes()

        timestamp = int(time.time())

        original_extension = (
            os.path.splitext(file_path.name)[1]
            or ".jpg"
        )

        # -----------------------------------------------------
        # Convert RAW to JPEG if necessary
        # -----------------------------------------------------

        print("Preparing image for background removal...")

        if original_extension.lower() in (
            ".nef",
            ".nrw"
        ):

            with rawpy.imread(
                io.BytesIO(image_data)
            ) as raw_image:

                full_resolution_image = (
                    raw_image.postprocess()
                )

            jpeg_buffer = io.BytesIO()

            Image.fromarray(
                full_resolution_image
            ).save(
                jpeg_buffer,
                format="JPEG",
                quality=95
            )

            image_data_for_rembg = (
                jpeg_buffer.getvalue()
            )

        else:

            image_data_for_rembg = image_data

        # -----------------------------------------------------
        # Remove background
        # -----------------------------------------------------

        print("Removing background...")

        image_without_background = remove(
            image_data_for_rembg
        )

        # -----------------------------------------------------
        # Save transparent PNG
        # -----------------------------------------------------

        capture_timestamp = time.strftime("%Y%m%d_%H%M%S")
        background_removed_path = os.path.join(
            CAPTURE_FOLDER,
            f"{capture_timestamp}_transparent.png"
        )

        with open(background_removed_path, "wb") as output_file:
            output_file.write(image_without_background)

        print(
            "Background-removed image saved to: "
            f"{background_removed_path}"
        )

        return True

    except gp.GPhoto2Error as e:

        print(
            f"Camera error capturing image: {e}"
        )

        return False

    except Exception as e:

        print(
            f"Image processing error: {e}"
        )

        return False

# =============================================================
# Main Live View
# =============================================================

def stream_live_view():

    camera = gp.Camera()

    initialized = False

    hand_detector = None

    try:

        # =====================================================
        # Initialize camera
        # =====================================================

        camera.init()

        initialized = True

        print(
            "Nikon D7000 initialized."
        )

        # =====================================================
        # Initialize MediaPipe
        # =====================================================

        print(
            "Starting MediaPipe hand detector..."
        )

        hand_detector = (
            create_hand_detector()
        )

        print(
            "MediaPipe ready."
        )

        # =====================================================
        # Gesture state
        # =====================================================

        open_hand_start = None

        gesture_triggered = False

        # =====================================================
        # Live View
        # =====================================================

        live_view_active = True

        frame_timestamp_ms = 0

        while True:

            # =================================================
            # Get Live View frame
            # =================================================

            if live_view_active:

                camera_file = (
                    camera.capture_preview()
                )

                file_data = (
                    camera_file.get_data_and_size()
                )

                data_bytes = (
                    memoryview(
                        file_data
                    ).tobytes()
                )

                image_array = np.frombuffer(
                    data_bytes,
                    dtype=np.uint8
                )

                frame = cv2.imdecode(
                    image_array,
                    cv2.IMREAD_COLOR
                )

                if frame is None:

                    continue

                # =================================================
                # MediaPipe
                # =================================================

                rgb_frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB
                )

                mp_image = mp.Image(
                    image_format=(
                        mp.ImageFormat.SRGB
                    ),
                    data=rgb_frame
                )

                frame_timestamp_ms += 33

                results = (
                    hand_detector.detect_for_video(
                        mp_image,
                        frame_timestamp_ms
                    )
                )

                open_hand = False

                # =================================================
                # Process detected hand
                # =================================================

                if results.hand_landmarks:

                    hand_landmarks = (
                        results.hand_landmarks[0]
                    )

                    open_hand = is_one_finger_up(
                        hand_landmarks
                    )

                    draw_gesture_progress(
                        frame,
                        hand_landmarks,
                        0.0
                    )


                # =================================================
                # Gesture logic
                # =================================================

                if (
                    open_hand
                    and not gesture_triggered
                ):

                    if open_hand_start is None:

                        open_hand_start = (
                            time.time()
                        )

                    elapsed = (
                        time.time()
                        -
                        open_hand_start
                    )

                    progress = min(
                        elapsed
                        /
                        GESTURE_HOLD_TIME,
                        1.0
                    )

                    draw_gesture_progress(
                        frame,
                        hand_landmarks,
                        progress,
                    )

                    if (
                        elapsed
                        >=
                        GESTURE_HOLD_TIME
                    ):

                        print(
                            "Open hand gesture triggered!"
                        )

                        gesture_triggered = True

                        open_hand_start = None

                else:

                    if not open_hand:

                        open_hand_start = None

                        gesture_triggered = False

                # =================================================
                # Display
                # =================================================

                cv2.imshow(
                    "Live View",
                    frame
                )

            # =================================================
            # Keyboard
            # =================================================

            key = cv2.waitKey(1) & 0xFF

            # -------------------------------------------------
            # Space OR open hand
            # -------------------------------------------------

            if (
                key == ord(" ")
                or gesture_triggered
            ):

                gesture_triggered = False

                open_hand_start = None

                # -------------------------------------------------
                # Stop Live View
                # -------------------------------------------------

                live_view_active = False

                cv2.destroyWindow(
                    "Live View"
                )

                time.sleep(
                    0.2
                )

                # -------------------------------------------------
                # Capture
                # -------------------------------------------------

                capture_photo(
                    camera
                )

                # -------------------------------------------------
                # Resume Live View
                # -------------------------------------------------

                print(
                    "Resuming live view..."
                )

                time.sleep(
                    0.5
                )

                live_view_active = True

            # -------------------------------------------------
            # Quit
            # -------------------------------------------------

            elif key == ord("q"):

                break

    except Exception as e:

        print(
            f"Error: {e}"
        )

        raise

    finally:

        cv2.destroyAllWindows()

        if hand_detector:

            hand_detector.close()

        if initialized:

            camera.exit()

        print(
            "Camera closed."
        )


# =============================================================
# Main
# =============================================================

if __name__ == "__main__":

    stream_live_view()
