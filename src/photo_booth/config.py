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
DROPBOX_ACCESS_TOKEN = os.environ.get("PHOTOBOOTH_DROPBOX_ACCESS_TOKEN", "sl.u.AG1CN92E-Wj7iimh73zQKNar29EB1a3raOIHGnJwl5Th-igxe4hBpGIjavWCkYAdDsgyLNaivRZkr5DrbZE-_1oM5cAClrI2i0bqMqMeBCcOMtNQOmmlCAaG_6BYxUPuWZvpieW38UYfy66qADUjstTLahuaQl-jWibUW7nFRiCpH-VJKevIbzqlbuy7wECme1mhEulWa7Sa5lNMoSqsM9t4z7wYc6vVLOsK60YrUHLibzp6loVqRhYXi455SigoIqQNgUkXhYZCbkNpMEcJ3348NnjCuC2caCHvALA0UCrJ72WW2iDo-4Xj60YTJ-438ZygfDU5k4r55RqtFDmgt7C93c562XeQnf3nZ6xV07YouTB8BZu6KPjVYrfzkfgt_cJjlF1JaL8E6DKErxFkIB1PRG9f6gYbKNLE7i6H3fqI0Zo-UXo5_ZqxHZ1l72ahiBuTkY1s1GMYf0o5K1lAOnkfGD5XIPc7Dqt61k9TUzm05NQAvlCL2y8HKUfEg8wlQpjQuBBJQvnUi1UrraWJUpgHNvWNc9EZcozLzaxDwKglJjaYYn50McuNREg2G5t8mF27iLZ0Al6aeotBaEbcROoFOGm0WfiF9RoDJgLx6CHLwDO4ZIfyIohG8bilQYTso6pXxQJgVPBiCUSFMZH7gyXyRYrZiMOF4z-fFzafaRr75kg7Vmxxz6i970Wny0_LNcX9QWCZBFT8hN0pyk9vho-epmcnNWrKOxiu3uuXv2wrHakNtmdiQqZfV8-DYCGQE3-LKbLvoXaHItT5gZleo_tFYDks5f1fN63H6tYvYPiKijIU2UOF7OpuR8320Qgny7DXsNepftkVxC81p1IBUFoqlRqnR027slzjAv7q-m7EiCBAlhytFvyNQXBG0XEiCF1gu1SpOH_3xJ_yEjZ2rUBBZX5WGpX6XIfWH8T7Tr0QpBSnHhujflWnYd4QWzD6PlyDCM5vqLLjHl-lmWQHvM-uwYJT-Q2JMpH8JrB2kehI3BUhWqMtjZtTo4GkwUP6IDInGTP156N_eOhBrLWkpg3ElA_cOSpfcUh85YK1_Ot0kdRte_WF4cSHM8N0WHtRDFL_CKT04XJyg0Zsnka8kxLdbwZrhBARj3yPQbQOEHb7JZPbj4ozLuA9-GV3oq9yxP2IW_rRyd9ZgCbOOuNGoOO3CmzmoKY3jdTrsaO7e2feAujhaTM9XB1idOl6PuapxCyZgfcKX_80Yu-MVzDi7Un-h8J73LA2lv3594bw_k5pJdlELBn71X31aTlWrnqAFTToxgjazab_Y-yDX9nygABvprDdm894Uwq0BYOaXVEDnzsSwBr93MEUoy_cRmflAS8")
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