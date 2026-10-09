"""Photo capture and image processing."""

import io
import os
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime

import gphoto2 as gp
import rawpy
from PIL import Image
from rembg import remove

from .camera import autofocus, configure_camera
from .config import CAPTURE_FOLDER


def _process_captured_image(image_data, original_extension):
    """Convert a captured image and remove its background."""

    if original_extension.lower() in (".nef", ".nrw"):
        with rawpy.imread(io.BytesIO(image_data)) as raw_image:
            full_resolution_image = raw_image.postprocess()

        jpeg_buffer = io.BytesIO()
        Image.fromarray(full_resolution_image).save(
            jpeg_buffer,
            format="JPEG",
            quality=95,
        )
        image_data_for_rembg = jpeg_buffer.getvalue()
    else:
        image_data_for_rembg = image_data

    image_without_background = remove(image_data_for_rembg)

    capture_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = CAPTURE_FOLDER / f"{capture_timestamp}_transparent.png"

    with open(output_path, "wb") as output_file:
        output_file.write(image_without_background)

    return output_path


def _report_processing_result(future: Future):
    try:
        output_path = future.result()
    except Exception as exc:
        print(f"Image processing error: {exc}")
    else:
        print(f"Background-removed image saved to: {output_path}")


def capture_photo(camera, image_executor: ThreadPoolExecutor):
    """Capture a photo and queue image processing in the background."""

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

        print("Photo captured; processing in the background...")
        image_future = image_executor.submit(
            _process_captured_image,
            image_data,
            original_extension,
        )
        image_future.add_done_callback(_report_processing_result)

        return True

    except gp.GPhoto2Error as exc:
        print(f"Camera error capturing image: {exc}")
        return False

    except Exception as exc:
        print(f"Error capturing image: {exc}")
        return False