"""Nikon D7000 camera configuration and autofocus."""

import time

import gphoto2 as gp


def configure_camera(camera):
    """Configure the Nikon D7000 for photo booth photography."""

    try:
        print("Configuring camera...")
        context = gp.Context()

        # --------------------------------------------------
        # ISO: 200
        # --------------------------------------------------
        print("Setting ISO to 200")

        try:
            config = camera.get_config(context)
            settings = config.get_child_by_name("imgsettings")
            iso_widget = settings.get_child_by_name("iso")

            iso_widget.set_value("200")
            camera.set_config(config, context)

            time.sleep(0.3)

            # Verify ISO
            config = camera.get_config(context)
            settings = config.get_child_by_name("imgsettings")
            iso_widget = settings.get_child_by_name("iso")

            print(f"ISO reported by camera: {iso_widget.get_value()}")

        except gp.GPhoto2Error as exc:
            print(f"Could not set ISO: {exc}")

        # --------------------------------------------------
        # Aperture: f/8
        # --------------------------------------------------
        config = camera.get_config(context)
        settings = config.get_child_by_name("capturesettings")
        widget = settings.get_child_by_name("f-number")

        print("Setting F-Number to f/8")

        widget.set_value("f/8")
        camera.set_config(config, context)

        # --------------------------------------------------
        # Shutter speed: 1/160 second
        # --------------------------------------------------
        config = camera.get_config(context)
        settings = config.get_child_by_name("capturesettings")
        widget = settings.get_child_by_name("shutterspeed")

        print("Setting Shutter Speed to 0.0062s")

        widget.set_value("0.0062s")
        camera.set_config(config, context)

        # --------------------------------------------------
        # Nikon flash mode: iTTL
        # --------------------------------------------------
        config = camera.get_config(context)
        settings = config.get_child_by_name("capturesettings")
        widget = settings.get_child_by_name("nikonflashmode")

        print("Nikon Flash Mode set to iTTL")

        widget.set_value("iTTL")
        camera.set_config(config, context)

        # --------------------------------------------------
        # Display current settings
        # --------------------------------------------------
        config = camera.get_config(context)
        settings = config.get_child_by_name("capturesettings")

        print("Camera configuration:")

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

                print(f"  {label}: {value}")

            except gp.GPhoto2Error as exc:
                print(f"  {label}: unavailable ({exc})")

    except gp.GPhoto2Error as exc:
        print(f"Could not configure camera: {exc}")


def autofocus(camera, context):
    """Trigger autofocus on the Nikon D7000."""

    try:
        print("Reading autofocus control...")

        widget = camera.get_single_config(
            "autofocusdrive",
            context
        )

        print(f"Autofocus widget: {widget.get_name()}")
        print(f"Widget type: {widget.get_type()}")
        print(f"Current value: {widget.get_value()}")

        widget.set_value(1)

        print("Sending autofocus command...")

        camera.set_single_config(
            "autofocusdrive",
            widget,
            context
        )

        print("Autofocus command accepted.")

        time.sleep(1.0)

        return True

    except gp.GPhoto2Error as exc:
        print(f"gphoto2 autofocus error: {exc}")
        return False

    except Exception as exc:
        print(f"Unexpected autofocus error: {exc}")
        return False