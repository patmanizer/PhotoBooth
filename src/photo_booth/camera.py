"""Nikon D7000 camera configuration and autofocus."""

import time

import gphoto2 as gp

from .config import (
    CAMERA_APERTURE,
    CAMERA_FLASH_MODE,
    CAMERA_ISO,
    CAMERA_SHUTTER_SPEED,
)
from .logging_utils import log


def configure_camera(camera):
    """Configure the Nikon D7000 for photo booth photography."""

    try:
        log("Configuring camera...")
        context = gp.Context()

        # --------------------------------------------------
        # ISO
        # --------------------------------------------------
        log(f"Setting ISO to {CAMERA_ISO}")

        try:
            config = camera.get_config(context)
            settings = config.get_child_by_name("imgsettings")
            iso_widget = settings.get_child_by_name("iso")

            iso_widget.set_value(CAMERA_ISO)
            camera.set_config(config, context)

            time.sleep(0.3)

            # Verify ISO
            config = camera.get_config(context)
            settings = config.get_child_by_name("imgsettings")
            iso_widget = settings.get_child_by_name("iso")

            log(f"ISO reported by camera: {iso_widget.get_value()}")

        except gp.GPhoto2Error as exc:
            log(f"Could not set ISO: {exc}")

        # --------------------------------------------------
        # Aperture
        # --------------------------------------------------
        config = camera.get_config(context)
        settings = config.get_child_by_name("capturesettings")
        widget = settings.get_child_by_name("f-number")

        log(f"Setting F-Number to {CAMERA_APERTURE}")

        widget.set_value(CAMERA_APERTURE)
        camera.set_config(config, context)

        # --------------------------------------------------
        # Shutter speed: 1/160 second
        # --------------------------------------------------
        config = camera.get_config(context)
        settings = config.get_child_by_name("capturesettings")
        widget = settings.get_child_by_name("shutterspeed")

        log(f"Setting Shutter Speed to {CAMERA_SHUTTER_SPEED}")

        widget.set_value(CAMERA_SHUTTER_SPEED)
        camera.set_config(config, context)

        # --------------------------------------------------
        # Nikon flash mode: iTTL
        # --------------------------------------------------
        config = camera.get_config(context)
        settings = config.get_child_by_name("capturesettings")
        widget = settings.get_child_by_name("nikonflashmode")

        log(f"Nikon Flash Mode set to {CAMERA_FLASH_MODE}")

        widget.set_value(CAMERA_FLASH_MODE)
        camera.set_config(config, context)

        # --------------------------------------------------
        # Display current settings
        # --------------------------------------------------
        config = camera.get_config(context)
        settings = config.get_child_by_name("capturesettings")

        log("Camera configuration:")

        for label, widget_name in (
            ("Exposure", "expprogram"),
            ("Aperture", "f-number"),
            ("Shutter", "shutterspeed"),
            ("Flash", "nikonflashmode"),
        ):
            try:
                value = settings.get_child_by_name(
                    widget_name
                ).get_value()

                log(f"  {label}: {value}")

            except gp.GPhoto2Error as exc:
                log(f"  {label}: unavailable ({exc})")

    except gp.GPhoto2Error as exc:
        log(f"Could not configure camera: {exc}")


def autofocus(camera, context):
    """Trigger autofocus on the Nikon D7000."""

    try:
        log("Reading autofocus control...")

        widget = camera.get_single_config(
            "autofocusdrive",
            context
        )

        log(f"Autofocus widget: {widget.get_name()}")
        log(f"Widget type: {widget.get_type()}")
        log(f"Current value: {widget.get_value()}")

        widget.set_value(1)

        log("Sending autofocus command...")

        camera.set_single_config(
            "autofocusdrive",
            widget,
            context
        )

        log("Autofocus command accepted.")

        time.sleep(1.0)

        return True

    except gp.GPhoto2Error as exc:
        log(f"gphoto2 autofocus error: {exc}")
        return False

    except Exception as exc:
        log(f"Unexpected autofocus error: {exc}")
        return False