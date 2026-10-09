"""MediaPipe hand detector initialization."""

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from .config import (
    MODEL_PATH,
    MIN_HAND_DETECTION_CONFIDENCE,
    MIN_HAND_PRESENCE_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
)


def create_hand_detector():
    """Create and return the MediaPipe hand detector."""

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Could not find MediaPipe model: {MODEL_PATH}"
        )

    base_options = python.BaseOptions(
        model_asset_path=str(MODEL_PATH)
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
        ),
    )

    return vision.HandLandmarker.create_from_options(options)