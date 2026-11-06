"""Background removal backends for desktop and Raspberry Pi deployments."""

import io
from pathlib import Path

import numpy as np
from PIL import Image
from rembg import new_session, remove

from .config import MODNET_HEF_PATH
from .logging_utils import log

_FALLBACK_MODEL = "bria-rmbg"
_background_removal_session = None
_background_removal_model_name = None


def _is_raspberry_pi():
    """Return whether this process is running on Raspberry Pi hardware."""

    model_path = Path("/proc/device-tree/model")
    return model_path.is_file() and b"Raspberry Pi" in model_path.read_bytes()


def _tensor_shape(tensor, tensor_name):
    """Return a fixed, single-image tensor shape without its batch dimension."""

    shape = tuple(int(dimension) for dimension in tensor.shape)
    if len(shape) == 4:
        if shape[0] != 1:
            raise ValueError(f"MODNet {tensor_name} batch size must be 1, got {shape[0]}.")
        shape = shape[1:]
    if len(shape) != 3 or any(dimension <= 0 for dimension in shape):
        raise ValueError(f"MODNet {tensor_name} must have a fixed 3D image shape, got {shape}.")
    return shape


def _image_layout(shape, channels, tensor_name):
    """Return image dimensions and channel layout for an HWC or CHW tensor."""

    if shape[-1] == channels:
        return shape[0], shape[1], "HWC"
    if shape[0] == channels:
        return shape[1], shape[2], "CHW"
    raise ValueError(
        f"MODNet {tensor_name} must have {channels} channels in HWC or CHW layout, "
        f"got {shape}."
    )


class _HailoModNetSession:
    """Run a fixed-shape MODNet HEF through the HailoRT Python API."""

    def __init__(self, hef_path):
        try:
            from hailo_platform import FormatType, VDevice
        except ImportError as error:
            raise RuntimeError(
                "A MODNet HEF is configured, but hailo_platform is unavailable. "
                "Install the HailoRT Python bindings for the AI HAT 2."
            ) from error

        self._device = VDevice()
        self._model = self._device.create_infer_model(str(hef_path))
        if len(self._model.inputs) != 1 or len(self._model.outputs) != 1:
            raise ValueError("The MODNet HEF must have exactly one input and one output.")

        self._model.input().set_format_type(FormatType.FLOAT32)
        self._model.output().set_format_type(FormatType.FLOAT32)
        self._input_model_shape = tuple(int(dimension) for dimension in self._model.input().shape)
        self._input_shape = _tensor_shape(self._model.input(), "input")
        self._input_height, self._input_width, self._input_layout = _image_layout(
            self._input_shape,
            3,
            "input",
        )
        self._output_model_shape = tuple(
            int(dimension) for dimension in self._model.output().shape
        )
        self._output_shape = _tensor_shape(self._model.output(), "output")
        self._output_height, self._output_width, self._output_layout = _image_layout(
            self._output_shape,
            1,
            "output",
        )
        self._output_name = self._model.outputs[0].name
        self._configuration = self._model.configure()
        self._configured_model = self._configuration.__enter__()

    def remove_background(self, image_data):
        """Return the input image as a PNG with MODNet's predicted alpha matte."""

        with Image.open(io.BytesIO(image_data)) as image:
            source = image.convert("RGB")

        fitted = source.copy()
        fitted.thumbnail(
            (self._input_width, self._input_height),
            Image.Resampling.BILINEAR,
        )
        offset_x = (self._input_width - fitted.width) // 2
        offset_y = (self._input_height - fitted.height) // 2
        model_image = Image.new("RGB", (self._input_width, self._input_height), (128, 128, 128))
        model_image.paste(fitted, (offset_x, offset_y))

        input_tensor = (np.asarray(model_image, dtype=np.float32) - 127.5) / 127.5
        if self._input_layout == "CHW":
            input_tensor = np.transpose(input_tensor, (2, 0, 1))
        if len(self._input_model_shape) == 4:
            input_tensor = input_tensor[np.newaxis, ...]
        input_tensor = np.ascontiguousarray(input_tensor)

        output_buffer = np.empty(self._output_model_shape, dtype=np.float32)
        bindings = self._configured_model.create_bindings(
            output_buffers={self._output_name: output_buffer},
        )
        bindings.input().set_buffer(input_tensor)
        self._configured_model.run([bindings], timeout=30000)
        matte = np.asarray(bindings.output().get_buffer(), dtype=np.float32)
        if len(self._output_model_shape) == 4:
            matte = matte[0]
        if self._output_layout == "HWC":
            matte = matte[:, :, 0]
        else:
            matte = matte[0, :, :]

        if matte.shape != (self._output_height, self._output_width):
            raise ValueError(
                "MODNet output must be a single-channel alpha matte, "
                f"got shape {matte.shape}."
            )

        matte_image = Image.fromarray(
            (np.clip(matte, 0.0, 1.0) * 255).astype(np.uint8),
        ).resize(
            (self._input_width, self._input_height),
            Image.Resampling.BILINEAR,
        )
        fitted_matte = matte_image.crop(
            (
                offset_x,
                offset_y,
                offset_x + fitted.width,
                offset_y + fitted.height,
            )
        )
        alpha = fitted_matte.resize(source.size, Image.Resampling.LANCZOS).convert("L")
        source.putalpha(alpha)

        output = io.BytesIO()
        source.save(output, format="PNG")
        return output.getvalue()


def get_background_removal_model_name():
    """Return the configured backend name for current platform and model files."""

    if _background_removal_model_name is not None:
        return _background_removal_model_name
    if _is_raspberry_pi() and MODNET_HEF_PATH.is_file():
        return "MODNet (AI HAT 2)"
    return _FALLBACK_MODEL


def get_background_removal_session():
    """Create the platform-appropriate background removal session on demand."""

    global _background_removal_session, _background_removal_model_name

    if _background_removal_session is None:
        if _is_raspberry_pi() and MODNET_HEF_PATH.is_file():
            log(f"Loading MODNet HEF for AI HAT 2: {MODNET_HEF_PATH}.")
            _background_removal_session = _HailoModNetSession(MODNET_HEF_PATH)
            _background_removal_model_name = "MODNet (AI HAT 2)"
        else:
            if _is_raspberry_pi():
                log(
                    f"MODNet HEF not found at {MODNET_HEF_PATH}; "
                    f"using {_FALLBACK_MODEL} until the HEF is installed."
                )
            log(f"Loading background removal model: {_FALLBACK_MODEL}.")
            _background_removal_session = new_session(_FALLBACK_MODEL)
            _background_removal_model_name = _FALLBACK_MODEL

    return _background_removal_session


def remove_background(image_data, session):
    """Remove an image background using the selected backend."""

    if isinstance(session, _HailoModNetSession):
        return session.remove_background(image_data)
    return remove(image_data, session=session)
