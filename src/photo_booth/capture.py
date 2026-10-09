"""Photo capture and image processing."""

import io
import os
import time

import gphoto2 as gp
import rawpy
from PIL import Image
from rembg import remove

from .camera import autofocus, configure_camera
from .config import CAPTURE_FOLDER


def capture_photo(camera):
    """Capture a photo and save a transparent PNG."""

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

        # --------------------------------------------------
        # Convert Nikon RAW to JPEG if necessary.
        # --------------------------------------------------
        print("Preparing image for background removal...")

        if original_extension.lower() in (".nef", ".nrw"):
            with rawpy.imread(
                io.BytesIO(image_data)
            ) as raw_image:
                full_resolution_image = raw_image.postprocess()

            jpeg_buffer = io.BytesIO()

            Image.fromarray(
                full_resolution_image
            ).save(
                jpeg_buffer,
                format="JPEG",
                quality=95,
            )

            image_data_for_rembg = jpeg_buffer.getvalue()

        else:
            image_data_for_rembg = image_data

        # --------------------------------------------------
        # Remove background.
        # --------------------------------------------------
        print("Removing background...")

        image_without_background = remove(
            image_data_for_rembg
        )

        # --------------------------------------------------
        # Save transparent PNG.
        # --------------------------------------------------
        capture_timestamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )

        output_path = CAPTURE_FOLDER / (
            f"{capture_timestamp}_transparent.png"
        )

        with open(output_path, "wb") as output_file:
            output_file.write(image_without_background)

        print(
            "Background-removed image saved to: "
            f"{output_path}"
        )

        return True

    except gp.GPhoto2Error as exc:
        print(f"Camera error capturing image: {exc}")
        return False

    except Exception as exc:
        print(f"Image processing error: {exc}")
        return False