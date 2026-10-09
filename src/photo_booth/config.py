"""Shared application configuration."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]

MODEL_PATH = PROJECT_ROOT / "hand_landmarker.task"
CAPTURE_FOLDER = PACKAGE_DIR / "captured_images"

# Gesture settings
GESTURE_HOLD_TIME = 2.0

# MediaPipe confidence settings
MIN_HAND_DETECTION_CONFIDENCE = 0.6
MIN_HAND_PRESENCE_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6