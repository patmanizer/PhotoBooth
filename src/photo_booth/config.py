"""Shared application configuration."""

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]

MODEL_PATH = PROJECT_ROOT / "resources" / "models" / "hand_landmarker.task"
MODNET_HEF_PATH = PROJECT_ROOT / "resources" / "models" / "modnet_photographic_portrait_matting.hef"
FONT_PATH = PROJECT_ROOT / "resources" / "font" / "SimpleHandmade.otf"
CAPTURE_FOLDER = PROJECT_ROOT / "captured_images"
OUTPUT_FOLDER = PROJECT_ROOT / "output"
RAW_FOLDER = PROJECT_ROOT / "raw"
SAVE_RAW_FILES = False
VIRTUAL_BACKDROP_ENABLED = True
DROPBOX_ACCESS_TOKEN = os.environ.get("PHOTOBOOTH_DROPBOX_ACCESS_TOKEN", "sl.u.AG2UnOBWFOix7WORLa5B5sbgh1u-3MT5WzqQ5NlOXz13du8e9-tMzZvkPWxconFgJJ6kbRsKpOnWL4wSXh5_dluzwq7spdpOx4Izo5KcYLPgVx1CFbySNHdZ0QqMvbyo_qTItK430vaXsxforZHOOE8V0GJ3jQ7pI869o_qz-xg4S6ybGgb2RwqbusJNzy0O0yxB19DNwb_Ky1uyzPwyDb8SXvUcvPEkButXqNn0okJt6epzC_DQUHKFt0WYRi5fSJB45-lNheyqvdbMVesV3ZdD9B3lQ3hhVEZHJoT964J-5Y75Dx2Veg6MyFFyinRNGPrPRrlSRwz014EAyeWZd5IJl59J0y2l8dtNr6w9cnHB_vlpZDEeKB26TAkG0D6pfBTI7iofdYbP-BMuHCP58uyHsy9laj04IuyB4yiq9-ApxD-u6StcYG7os1raWu_M4bGc3GpUWTojW_jyZK29IxXdFG8k_VR__LghP8cBlLrTyGQnpe_Fo0h6nAk2C7lQtsh1jsWvkGxiL2B4YmZTq2DXd5aqGnl5q71RWO4h-S_YlXVt7-Uonx25R6FB2ZzE8hP0ih7SgriyxA64F82nxDVpncz7jD8qW3QN4jdELZ3bvRtW7j3wkVSWctrGJT7NJLFzbvrJ7stLFor4_RZkd1gt2QI5QLAfyj3Y7TO940a9Lsb3AAGmH910Sczx8aX_0y5xUMfa8Iwth4eIgDSX1TaLE7MwU8NelDy3BbmHizALn1QUrGdlmR7ACjjt0LyRRSdz8he8R5YzPFuLRYsDLQ9z5T5ap1XPq3aWkTUt_oCC83DOxrD22eVVrEwUZ3K2H609dnD4TOYSYwjO-1-E7sgfu7ADngc42KnGz3se6PzJQd1d2g3KOBuFotuCqzaXuGljmuLUqGC-Qwub56BcoTxIg_fEGm14ZHKud6gNHqcAB9zT72q9Frt0bAC_0z3pgPbsmXRSADybgNmJ9qXZpnjPKqiGsdBY-1bqVtZz9KMupZwHA5FdWAArCEZj_MQKuMLz1rWkfQI1GbE4h6T6F0ELT4u5m93iOLiI7RtsTlTfgc7NbFHbcD3i3YgH80wnkUyLUjsTgLNtdggFAt8sIEQDcpxRLupz26MVKmw9GVOInD8MC4iKABOcmTlRkY5BZm_KCo-6FOPJwABiq6oIDB1d13T9bpC1SQpxLTqQvuKEP3LWLxpLJWjfX9uoPRfUShWhJGxB156K5hQaUI53kN9IO_l5UN0Cd4E6AQQjAKNpDjfpdgbhcOq-WQ_AWke2a8KuZD7R_tEGB4sxn7L-iZZ7L2hUSZ2knikOERVa9oHaO2SjRga8MjX7NtEQKP47_Hk")
DROPBOX_UPLOAD_PATH = "/PhotoBooth/output"
DROPBOX_QR_DISPLAY_SECONDS = 5.0
INDIVIDUAL_BACKDROP_FOLDER = PROJECT_ROOT / "resources" / "individual_backdrop"
INDIVIDUAL_FOREGROUND_FOLDER = PROJECT_ROOT / "resources" / "individual_foreground"
COLLAGE_BACKGROUND_FOLDER = PROJECT_ROOT / "resources" / "collage_background"
MAIN_FOREGROUND_FOLDER = PROJECT_ROOT / "resources" / "main_foreground"

# Camera settings
CAMERA_ISO = "200"
CAMERA_APERTURE = "f/5.6"
CAMERA_SHUTTER_SPEED = "0.0062s"
CAMERA_FLASH_MODE = "iTTL"

# Gesture settings
GESTURE_HOLD_TIME = 2.0

# Capture countdown settings
PHOTO_PROMPTS = (
    "Strike your best red-carpet pose!",
    "Give us your movie-star smile!",
    "Show off your most dramatic look!",
    "Pose like the star of the show!",
    "Share a little Hollywood glamour!",
    "Give the camera your award-winning smile!",
    "Strike a pose worthy of a movie poster!",
    "Show us your leading-role energy!",
    "Turn up the glamour and own the spotlight!",
    "Give us a look that says, 'I'm famous!'",
    "Pose like the paparazzi are watching!",
    "Make this your close-up moment!",
    "Show off your signature star pose!",
    "Bring the drama, darling!",
    "Smile like you just won an Oscar!",
    "Give us a little sparkle and confidence!",
    "Pose like you're walking the red carpet!",
    "Show us your best Hollywood expression!",
    "Take center stage and shine!",
    "Make this shot unforgettable!",
)
PROCESSING_PROMPTS = (
    "Hold up! Your awesomeness is loading!",
    "Warning! Too many good looks detected. Processing!",
    "Hang tight! We're making you look… well, still awesome!",
    "Processing your face… Please remain fabulous!",
    "Almost there! Our computer is thinking really hard!",
    "Stay cool! Your pixels are having a meeting!",
    "Please wait… Your smile is taking the scenic route!",
    "Just a sec! Even your good looks need processing!",
    "Whoa! That's a lot of good looks to process!",
    "Keep calm! Your face is loading in HD!",
    "Please wait… Your smile is under quality inspection!",
    "Hold on! We're counting all those beautiful pixels!",
    "Loading your best side… Please stand by!",
    "Almost done! Our computer needs a coffee break!",
    "Warning! Smile overload! System needs a moment!",
    "Be patient! Great photos don't rush themselves!",
    "Hold your horses! Your fabulousness is being processed!",
    "Even awesome takes a second! Hang tight!",
    "Turning your photo into a masterpiece!",
    "Beep boop! Calculating your level of fabulousness…",
    "Our pixels are working overtime!",
    "Don't blink! Your awesomeness is loading!",
    "Drumroll, please! Your masterpiece is almost ready!",
)
PROMPT_DISPLAY_SECONDS = 2.0
COUNTDOWN_SECONDS = 5

# MediaPipe confidence settings
MIN_HAND_DETECTION_CONFIDENCE = 0.6
MIN_HAND_PRESENCE_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6