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
DROPBOX_ACCESS_TOKEN = "sl.u.AG3vcDdLdIg1gvhUXEjdRo4juyXzm8GnWTZNfcvZq8yzODeGL1hcZjL_xsaoWTEczGWa3idvx555Aex7Y6dNvZCww6Cct1OSFzrYmWCTYTmqlbrPSp7nFe1fb6lCODDS8RXd0TkA_3RuLJua4Vy_kdtAmkiHi5mhu2OpstoBlrUTsLlzMmxDeeBRi5UBPL-HC-s66FrMc2g8m8CNxWRthTFKGZTPxsO-2AJloFiQQVIk9ZIibQfxLcbSk1pDGG83odRGuJ9C5RGTzXlWAKIUHN9wozc0wq1iOhW35YygRasvW-06mUQmXkAEyWIiMwkN79M2tah0EbVtcKslYYjhHc7rrbQfoKkntm2U-3SeU22tWojcgxcGO_7hUzW0Ctk09OLOGbjdER4HqUq0q_3JRNSPYrkNg69zCfsR0B5fhq8Ja9XgYis17-PxQp7UJLuQxKo3IxtLh8aZ7xXLL8KaD1wGluKBU59Ujj1TseB0ljjKPgIjPyixTUVfszbhjrzFPpWn3JtwWgAB38k6YxDOjhGxGsw_pXfSO03UzHRKXlK52dAyI-SKvzoMVjVoMFx19muenfHhXlvAthkfaFkIfwTyllXXdxa0OAOYh6Qhf_hRUZ9GVxVN_mKYxCTI7-6QAE3Dg1mNOMDvvEitceF1V83kuwlJpYg3zqw0XFMm0-XSKkS57vqPXFwLek07VyI03tvRbtsbXwZngUSwFPaGzKdGVdrFvE1TngEOvZ5UY3z-75II3L-sdScRB_lZuhEqYqwSav-vRucqHuqJbDPj9-qwS84HuxFIw8XZJIGHX26ZByD0bq_NzHPSaU54kuoFiTuELZ7LFLiLQfgCg65vfM7r4KY4SY1jeRG3Z-RcjCV49cr1MBMeXulAYB8UR53Z6R_t-61Xe24seDvQPyc_BG_5su-trrDI9ZV3ouDKGURsih9czYiepci9p7nYKggBArB-ad__5adevhkjfcAzauhVlrFh2Z4iRZzHcH6cRYdc4nXDWvBRJV6c-OygYkNFif4JXj8BD78528T5o3084wcKV6LMxAWHen8yBuPtW9IHIFdISSmmbiFhkMNnt1tdtxICanRNZyy5Y7G2ch2ccU_kqcXPXXVYVMjC3RxWYXF-nasGJFhpUe8psW7rwGtlUJqqCx21iJLjR6SpzX8nQmjj06TNQ8fJSdjT57t4kOzm-oM4Joq1BkvFarZyW_WOihUdfnFwqGChDbGrZMx5o9HYqbKoOFqcs1N2KJhg8iwtba9EGokqG5fLG3BWYJyCw24WSzDcZQfDL_b5JBcDEgKcqf9pz8euMI2fJ_-43aWw0C1A4VlOUtFWLsSBuFfUXiQ"
DROPBOX_REFRESH_TOKEN = "-yNTTHMpAd8AAAAAAAAAAWEqHuT3efbuSnDeBx7jJRFco7n3U6T26qQsWiHBMrKd"
DROPBOX_APP_KEY = "7ai9m6n645biidw"
DROPBOX_APP_SECRET = "u1vdrkimmj0qrrn"
DROPBOX_UPLOAD_PATH = "/PhotoBooth/output"
DROPBOX_QR_DISPLAY_SECONDS = 12.0
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