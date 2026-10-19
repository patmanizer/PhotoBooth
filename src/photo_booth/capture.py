"""Photo capture and image processing."""

import io
import math
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

import gphoto2 as gp
import rawpy
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from rembg import remove

from .camera import autofocus, configure_camera
from .foregrounds import fit_foreground
from .config import (
    CAPTURE_FOLDER,
    COLLAGE_BACKGROUND_FOLDER,
    INDIVIDUAL_BACKDROP_FOLDER,
    MAIN_FOREGROUND_FOLDER,
    OUTPUT_FOLDER,
    RAW_FOLDER,
    SAVE_RAW_FILES,
    VIRTUAL_BACKDROP_ENABLED,
)

_BACKDROP_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}
_COLLAGE_BACKGROUND_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}
_backdrop_index = 0
_main_foreground_index = 0


@dataclass(frozen=True)
class CapturedPhoto:
    """Camera image data and settings waiting for post-capture processing."""

    image_data: bytes
    original_extension: str
    foreground_path: Path
    crop_to_portrait: bool
    apply_individual_foreground: bool


def _next_backdrop_path():
    """Return the next supported individual_backdrop in alphabetical cycle order."""

    global _backdrop_index

    if not INDIVIDUAL_BACKDROP_FOLDER.is_dir():
        raise FileNotFoundError(
            f"Individual backdrop folder not found: {INDIVIDUAL_BACKDROP_FOLDER}"
        )

    backdrops = sorted(
        (
            path
            for path in INDIVIDUAL_BACKDROP_FOLDER.iterdir()
            if path.is_file()
            and path.suffix.lower() in _BACKDROP_EXTENSIONS
        ),
        key=lambda path: path.name.lower(),
    )
    if not backdrops:
        raise FileNotFoundError(
            f"No supported individual_backdrop images found in {INDIVIDUAL_BACKDROP_FOLDER}"
        )

    backdrop_path = backdrops[_backdrop_index % len(backdrops)]
    _backdrop_index += 1

    return backdrop_path


def _random_collage_background_path():
    """Choose a supported collage background image at random."""

    if not COLLAGE_BACKGROUND_FOLDER.is_dir():
        raise FileNotFoundError(
            f"Collage background folder not found: {COLLAGE_BACKGROUND_FOLDER}"
        )

    backgrounds = [
        path
        for path in COLLAGE_BACKGROUND_FOLDER.iterdir()
        if path.is_file()
        and path.suffix.lower() in _COLLAGE_BACKGROUND_EXTENSIONS
    ]
    if not backgrounds:
        raise FileNotFoundError(
            "No supported collage background images found in "
            f"{COLLAGE_BACKGROUND_FOLDER}"
        )

    return random.choice(backgrounds)


def next_main_foreground_path():
    """Return the next main foreground in alphabetical cycle order."""

    global _main_foreground_index

    if not MAIN_FOREGROUND_FOLDER.is_dir():
        raise FileNotFoundError(
            f"Main foreground folder not found: {MAIN_FOREGROUND_FOLDER}"
        )

    foregrounds = sorted(
        (
            path
            for path in MAIN_FOREGROUND_FOLDER.iterdir()
            if path.is_file()
            and path.suffix.lower() in _BACKDROP_EXTENSIONS
        ),
        key=lambda path: path.name.lower(),
    )
    if not foregrounds:
        raise FileNotFoundError(
            "No supported main foreground images found in "
            f"{MAIN_FOREGROUND_FOLDER}"
        )

    foreground_path = foregrounds[_main_foreground_index % len(foregrounds)]
    _main_foreground_index += 1

    return foreground_path


def _apply_main_foreground(image, foreground_path):
    """Overlay the selected main foreground over a finished output."""

    with Image.open(foreground_path) as foreground_image:
        foreground = fit_foreground(foreground_image, image.size)

    return Image.alpha_composite(image.convert("RGBA"), foreground)


def _process_captured_image(
    image_data,
    original_extension,
    foreground_path,
    crop_to_portrait,
    apply_individual_foreground,
):
    """Remove the background and composite subject and foreground."""

    # Convert Nikon RAW files to JPEG before image processing.
    if original_extension.lower() in (".nef", ".nrw"):
        with rawpy.imread(io.BytesIO(image_data)) as raw_image:
            full_resolution_image = raw_image.postprocess()

        jpeg_buffer = io.BytesIO()
        Image.fromarray(full_resolution_image).save(
            jpeg_buffer,
            format="JPEG",
            quality=95,
        )
        image_data_for_processing = jpeg_buffer.getvalue()
    else:
        image_data_for_processing = image_data

    if VIRTUAL_BACKDROP_ENABLED:
        image_without_background = remove(image_data_for_processing)
        backdrop_path = _next_backdrop_path()
    else:
        image_without_background = image_data_for_processing

    capture_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    with Image.open(io.BytesIO(image_without_background)) as subject_image:
        subject = subject_image.convert("RGBA")

    if VIRTUAL_BACKDROP_ENABLED:
        with Image.open(backdrop_path) as backdrop_image:
            backdrop = ImageOps.fit(
                backdrop_image.convert("RGBA"),
                subject.size,
                method=Image.Resampling.LANCZOS,
            )
        composite = Image.alpha_composite(backdrop, subject)
    else:
        composite = subject

    # Crop before adding the foreground so the overlay fits the portrait canvas.
    if crop_to_portrait:
        portrait_width = max(1, composite.height * 3 // 4)
        composite = ImageOps.fit(
            composite,
            (portrait_width, composite.height),
            method=Image.Resampling.LANCZOS,
        )

    output_path = CAPTURE_FOLDER / f"{capture_timestamp}_photo.png"
    final_image = composite
    if apply_individual_foreground:
        # Burst photos include the individual foreground before collage layout.
        with Image.open(foreground_path) as foreground_image:
            foreground = fit_foreground(foreground_image, composite.size)
        final_image = Image.alpha_composite(composite, foreground)

    final_image.save(output_path)

    return output_path


def _create_capture_output(
    captures: Sequence[Path],
    main_foreground_path: Path,
) -> Path:
    """Save a single photo or a landscape collage of a capture sequence."""

    if not captures:
        raise ValueError("Cannot create photo output without captured images")

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    output_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = OUTPUT_FOLDER / f"{output_timestamp}_photo.png"

    if len(captures) == 1:
        # Apply the main foreground once over the complete single-photo output.
        with Image.open(captures[0]) as source:
            final_image = _apply_main_foreground(
                source.convert("RGBA"),
                main_foreground_path,
            )
            final_image.save(output_path)
        return output_path

    # Use portrait captures as tilted prints on a landscape canvas.
    with Image.open(captures[0]) as first_image:
        first = first_image.convert("RGB")
    photo_height = first.height
    collage_size = (photo_height * 3 // 2, photo_height)
    background_path = _random_collage_background_path()
    with Image.open(background_path) as background_image:
        collage = ImageOps.fit(
            background_image.convert("RGB"),
            collage_size,
            method=Image.Resampling.LANCZOS,
        )

    count = len(captures)
    # Three columns are used for bursts of three or more; extra shots wrap
    # into additional rows while the overall output remains landscape.
    columns = min(count, 3)
    rows = math.ceil(count / columns)
    card_width = int(collage_size[0] * (0.42 if columns == 2 else 0.26))
    photo_margin = max(12, card_width // 16)
    inner_width = card_width - photo_margin * 2
    inner_size = (
        inner_width,
        inner_width * 4 // 3,
    )
    card_height = inner_size[1] + photo_margin * 2
    centers = []
    for row in range(rows):
        row_count = min(columns, count - row * columns)
        for column in range(row_count):
            # Space each row evenly, centering a final incomplete row.
            horizontal_position = (
                0.5
                if row_count == 1
                else (
                    0.27 + 0.46 * column / (row_count - 1)
                    if count == 2
                    else 0.225 + 0.55 * column / (row_count - 1)
                )
            )
            centers.append(
                (
                    int(collage_size[0] * horizontal_position),
                    (
                        photo_height // 2
                        if rows == 1
                        else int(photo_height * (0.28 + 0.44 * row))
                    ),
                )
            )
    angles = (-5, 5) if count == 2 else (-5, 3, -4)

    for index, image_path in enumerate(captures):
        if index == 0:
            photo = first
        else:
            with Image.open(image_path) as source:
                photo = source.convert("RGB")

        fitted_photo = ImageOps.fit(
            photo,
            inner_size,
            method=Image.Resampling.LANCZOS,
        )
        # Add only a soft drop shadow behind each tilted photo, with no card.
        photo_layer = Image.new(
            "RGBA",
            (
                fitted_photo.width + photo_margin * 2,
                fitted_photo.height + photo_margin * 2,
            ),
            (0, 0, 0, 0),
        )
        shadow = Image.new("RGBA", photo_layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle(
            (
                photo_margin,
                photo_margin,
                photo_margin + fitted_photo.width,
                photo_margin + fitted_photo.height,
            ),
            fill=(0, 0, 0, 100),
        )
        shadow = shadow.filter(
            ImageFilter.GaussianBlur(max(2, photo_height // 180))
        )
        photo_layer.alpha_composite(shadow)
        photo_layer.paste(
            fitted_photo.convert("RGBA"),
            (photo_margin, photo_margin),
        )
        rotated_photo = photo_layer.rotate(
            angles[index % len(angles)],
            resample=Image.Resampling.BICUBIC,
            expand=True,
        )
        position = (
            centers[index][0] - rotated_photo.width // 2,
            centers[index][1] - rotated_photo.height // 2,
        )
        collage.paste(rotated_photo, position, rotated_photo)

    # Apply the main foreground across the completed collage, not per photo.
    _apply_main_foreground(collage, main_foreground_path).save(output_path)
    return output_path


def save_capture_output(
    captures: Sequence[Path],
    main_foreground_path: Path,
) -> Path | None:
    """Create the output after the captured images are processed."""

    if not captures:
        return None

    output_path = _create_capture_output(captures, main_foreground_path)
    print(f"Photo output saved to: {output_path}")
    return output_path


def process_captured_photos(
    captured_photos: Sequence[CapturedPhoto],
) -> list[Path]:
    """Process every captured photo in sequence after the batch is captured."""

    processed_images: list[Path] = []
    processing_errors: list[Exception] = []
    for captured_photo in captured_photos:
        try:
            output_path = _process_captured_image(
                captured_photo.image_data,
                captured_photo.original_extension,
                captured_photo.foreground_path,
                captured_photo.crop_to_portrait,
                captured_photo.apply_individual_foreground,
            )
        except Exception as exc:
            print(f"Image processing error: {exc}")
            processing_errors.append(exc)
        else:
            print(f"Processed photo saved to: {output_path}")
            processed_images.append(output_path)

    if processing_errors:
        raise RuntimeError(
            f"Failed to process {len(processing_errors)} captured photo(s)"
        ) from processing_errors[0]

    return processed_images


def capture_photo(
    camera,
    foreground_path,
    crop_to_portrait=False,
    apply_individual_foreground=True,
) -> CapturedPhoto | None:
    """Capture and download a photo without starting post-processing."""

    context = gp.Context()
    CAPTURE_FOLDER.mkdir(parents=True, exist_ok=True)

    try:
        # --------------------------------------------------
        # Reinitialize camera connection.
        # This preserves the existing autofocus workaround.
        # --------------------------------------------------
        print("Reinitializing Nikon camera...")

        camera.exit()
        time.sleep(0.5)

        camera.init()
        time.sleep(0.5)

        configure_camera(camera)

        # --------------------------------------------------
        # Autofocus.
        # --------------------------------------------------
        print("Autofocusing...")

        autofocus_success = autofocus(
            camera,
            context,
        )

        if autofocus_success:
            print("Autofocus command sent successfully.")
        else:
            print(
                "Autofocus command failed. "
                "Continuing with capture..."
            )

        time.sleep(0.3)

        # --------------------------------------------------
        # Capture the actual photo.
        # --------------------------------------------------
        print("Capturing photo...")

        file_path = camera.capture(
            gp.GP_CAPTURE_IMAGE
        )

        print(f"Image captured: {file_path.name}")

        # --------------------------------------------------
        # Download the full-resolution image.
        # --------------------------------------------------
        camera_file = camera.file_get(
            file_path.folder,
            file_path.name,
            gp.GP_FILE_TYPE_NORMAL,
        )

        image_data = memoryview(
            camera_file.get_data_and_size()
        ).tobytes()

        original_extension = (
            os.path.splitext(file_path.name)[1]
            or ".jpg"
        )

        if SAVE_RAW_FILES:
            RAW_FOLDER.mkdir(parents=True, exist_ok=True)
            raw_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            raw_path = RAW_FOLDER / f"{raw_timestamp}_raw{original_extension}"
            raw_path.write_bytes(image_data)
            print(f"Raw photo saved to: {raw_path}")

        print("Photo captured; holding image for sequence processing...")
        return CapturedPhoto(
            image_data,
            original_extension,
            foreground_path,
            crop_to_portrait,
            apply_individual_foreground,
        )

    except gp.GPhoto2Error as exc:
        print(f"Camera error capturing image: {exc}")
        return None

    except Exception as exc:
        print(f"Error capturing image: {exc}")
        return None