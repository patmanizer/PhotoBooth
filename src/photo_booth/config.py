"""Shared application configuration."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]

MODEL_PATH = PROJECT_ROOT / "resources" / "hand_landmarker.task"
CAPTURE_FOLDER = PROJECT_ROOT / "captured_images"
BACKDROP_FOLDER = PROJECT_ROOT / "resources" / "backdrop"

# Gesture settings
GESTURE_HOLD_TIME = 2.0

# MediaPipe confidence settings
MIN_HAND_DETECTION_CONFIDENCE = 0.6
MIN_HAND_PRESENCE_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6