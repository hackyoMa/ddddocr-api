## DdddOcr API

_HTTP API service of DdddOcr_

### Startup

```bash
uv sync
uv run main.py
```

After startup:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health check: <http://localhost:8000/health>
- Current config: <http://localhost:8000/config>

### Environment

| Env | Default | Note |
| --- | --- | --- |
| `DA_OCR` | `True` | Whether to enable the OCR feature to recognize text in images. Mutually exclusive: When det=True, OCR is forced to be disabled. |
| `DA_DET` | `False` | Whether to enable the object detection feature, which is used to detect the positions of objects in an image. Mutually exclusive: setting `det=True` overrides `ocr=True`. |
| `DA_OLD` | `False` | Compatibility parameter; this will not change the model selection at this time (the default is to use the older model). |
| `DA_BETA` | `False` | Whether to use the beta OCR model (new model), which provides better recognition results for certain CAPTCHAs. Exclusivity: This option is mutually exclusive with the `old=True` parameter (though `old` is currently inactive). |
| `DA_USE_GPU` | `False` | Whether to use GPU acceleration. Dependencies: CUDA and the corresponding version of onnxruntime-gpu must be installed; otherwise, initialization will fail. |
| `DA_DEVICE_ID` | `0` | The GPU device ID to use. Dependency: Takes effect only when `use_gpu=True`; specifies which GPU device to use. |
| `DA_SHOW_AD` | `True` | Whether to display advertising information during initialization |
| `DA_IMPORT_ONNX_PATH` | "" | Path to the ONNX file for the custom model. Dependencies: When this parameter is set, the `charsets_path` parameter must also be provided; in this case, the `ocr/det` settings will be ignored. |
| `DA_CHARSETS_PATH` | "" | Path to the JSON file containing the custom character set. Dependencies: Must be used with `import_onnx_path`; otherwise, it is invalid. |
| `DA_MAX_IMAGE_BYTES` | `8MB` | Maximum number of bytes per image (input can be an int or a numeric string) |
| `DA_MAX_IMAGE_SIDE` | `4096` | Maximum number of pixels on the longest side of a single image (input can be an int or a numeric string) |
| `UVICORN_HOST` | `4096` | HTTP host |
| `UVICORN_PORT` | `4096` | HTTP port |
| `UVICORN_WORKERS` | `4096` | HTTP workers |
| `UVICORN_LOG_LEVEL` | `4096` | HTTP log level |

Docker example:

```bash
docker build -t ddddocr-api .
docker run -d -p 8000:8000 ddddocr-api
```

### API

OCR object detection uses the current process-level configuration of ddddocr. The `processing_time` in the response is in seconds.

#### Base64 OCR

```bash
curl -X POST http://localhost:8000/ocr \
  -H 'Content-Type: application/json' \
  -d '{"image":"data:image/png;base64,<BASE64>"}'
```

Optional Params：

- `probability`: Returns character probability information.
- `png_fix`: Fixes transparent PNG backgrounds.
- `color_filter_colors`: List of preset colors, such as `["red"]`.
- `color_filter_custom_ranges`: Custom HSV range.

#### Upload OCR

```bash
curl -X POST http://localhost:8000/ocr/file \
  -F 'file=@captcha.png'
```

#### Object Detection

```bash
curl -X POST http://localhost:8000/det \
  -H 'Content-Type: application/json' \
  -d '{"image":"<BASE64>"}'

curl -X POST http://localhost:8000/det/file \
  -F 'file=@target.png'
```

#### Slider Matching

```bash
curl -X POST http://localhost:8000/slide_match/file \
  -F 'target_image=@target.png' \
  -F 'background_image=@background.png'
```

The corresponding Base64 API endpoint is `POST /slide_match`, with request fields including `target_image`, `background_image`, and the optional `simple_target`. The slider image comparison API endpoints are `POST /slide_comparison` and `POST /slide_comparison/file`.
