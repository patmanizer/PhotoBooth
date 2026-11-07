# Raspberry Pi AI HAT 2 background removal

On Raspberry Pi, PhotoBooth uses the MODNet photographic portrait matting model on the AI HAT 2 when a compatible MODNet Hailo Executable Format (HEF) file is present. If the HEF is not present, background removal falls back to `bria-rmbg` through rembg. Other platforms continue to use `bria-rmbg`.

Install the HailoRT runtime and its `hailo_platform` Python bindings using the Raspberry Pi AI HAT 2 setup instructions. They must be available to the same Python environment that runs PhotoBooth.

Place a Hailo-10H-compatible MODNet HEF at:

```text
resources/models/modnet_photographic_portrait_matting.hef
```

Alternatively, set `PHOTOBOOTH_MODNET_HEF` to the HEF's path. The file is intentionally excluded from Git because it is a hardware-specific compiled model. The expected model has one fixed-shape RGB input and one single-channel alpha-matte output; the runtime handles either HWC or CHW tensor layout. MODNet's input is normalized to `[-1, 1]`, and the output matte is interpreted in `[0, 1]`.

The HEF must be compiled for the AI HAT 2's Hailo-10H. The MODNet source checkpoint or ONNX model is not itself a HEF and cannot be loaded by HailoRT directly. If a HEF is present but HailoRT cannot load it or the runtime is unavailable, PhotoBooth reports the error instead of silently switching backends.
