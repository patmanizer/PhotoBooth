"""Shared application configuration."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]

MODEL_PATH = PROJECT_ROOT / "resources" / "hand_landmarker.task"
FONT_PATH = PROJECT_ROOT / "resources" / "font" / "SimpleHandmade.otf"
CAPTURE_FOLDER = PROJECT_ROOT / "captured_images"
INDIVIDUAL_BACKDROP_FOLDER = PROJECT_ROOT / "resources" / "individual_backdrop"
INDIVIDUAL_FOREGROUND_FOLDER = PROJECT_ROOT / "resources" / "individual_foreground"

# Gesture settings
GESTURE_HOLD_TIME = 2.0

# Capture countdown settings
PHOTO_PROMPTS = (
    "Strike your best red-carpet pose",
    "Give us your movie-star smile",
    "Show off your most dramatic look",
    "Pose like the star of the show",
    "Share a little Hollywood glamour",
)
PROMPT_DISPLAY_SECONDS = 2.0
COUNTDOWN_SECONDS = 5

# MediaPipe confidence settings
MIN_HAND_DETECTION_CONFIDENCE = 0.6
MIN_HAND_PRESENCE_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6