"""Foreground image selection and live-view compositing."""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from .config import INDIVIDUAL_FOREGROUND_FOLDER

_FOREGROUND_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}


class ForegroundCycler:
    """Cycle through foreground images in alphabetical order."""

    def __init__(self):
        if not INDIVIDUAL_FOREGROUND_FOLDER.is_dir():
            raise FileNotFoundError(
                f"Individual foreground folder not found: {INDIVIDUAL_FOREGROUND_FOLDER}"
            )

        self._paths = sorted(
            (
                path
                for path in INDIVIDUAL_FOREGROUND_FOLDER.iterdir()
                if path.is_file()
                and path.suffix.lower() in _FOREGROUND_EXTENSIONS
            ),
            key=lambda path: path.name.lower(),
        )
        if not self._paths:
            raise FileNotFoundError(
                "No supported foreground images found in "
                f"{INDIVIDUAL_FOREGROUND_FOLDER}"
            )

        self._index = 0

    @property
    def current_path(self) -> Path:
        """Return the foreground currently shown in live view."""

        return self._paths[self._index]

    def advance(self):
        """Select the next foreground image, wrapping at the end."""

        self._index = (self._index + 1) % len(self._paths)


def load_foreground(path, size):
    """Load a foreground as a fitted BGRA image for OpenCV compositing."""

    with Image.open(path) as image:
        foreground = ImageOps.fit(
            image.convert("RGBA"),
            size,
            method=Image.Resampling.LANCZOS,
        )
        return cv2.cvtColor(
            np.asarray(foreground),
            cv2.COLOR_RGBA2BGRA,
        )


def overlay_foreground(frame, foreground):
    """Composite a transparent foreground image over a BGR frame."""

    height, width = frame.shape[:2]
    if foreground.shape[:2] != (height, width):
        foreground = cv2.resize(
            foreground,
            (width, height),
            interpolation=cv2.INTER_AREA,
        )

    alpha = foreground[:, :, 3:4].astype(np.float32) / 255
    frame[:] = (
        foreground[:, :, :3].astype(np.float32) * alpha
        + frame.astype(np.float32) * (1 - alpha)
    ).astype(np.uint8)
