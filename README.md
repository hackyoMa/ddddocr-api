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

### Environment

| Env | Default | Note |
| --- | --- | --- |
| `DA_OCR` | `True` | Whether to enable the OCR feature to recognize text in images. Mutually exclusive: When det=True, OCR is forced to be disabled. |
| `DA_DET` | `False` | Whether to enable the object detection feature, which is used to detect the positions of objects in an image. Mutually exclusive: setting `det=True` overrides `ocr=True`. |
| `DA_OLD` | `False` | Compatibility parameter; this will not change the model selection at this time (the default is to use the older model). |
| `DA_BETA` | `False` | Whether to use the beta OCR model (new model), which provides better recognition results for certain CAPTCHAs. Exclusivity: This option is mutually exclusive with the `old=True` parameter (though `old` is currently inactive). |
| `DA_USE_GPU` | `False` | Whether to use GPU acceleration. Dependencies: CUDA and the corresponding version of onnxruntime-gpu must be installed; otherwise, initialization will fail. |
| `DA_DEVICE_ID` | `0` | The GPU device ID to use. Dependency: Takes effect only when `use_gpu=True`; specifies which GPU device to use. |
| `DA_SHOW_AD` | `False` | Whether to display advertising information during initialization |
| `DA_IMPORT_ONNX_PATH` | "" | Path to the ONNX file for the custom model. Dependencies: When this parameter is set, the `charsets_path` parameter must also be provided; in this case, the `ocr/det` settings will be ignored. |
| `DA_CHARSETS_PATH` | "" | Path to the JSON file containing the custom character set. Dependencies: Must be used with `import_onnx_path`; otherwise, it is invalid. |
| `UVICORN_HOST` | `0.0.0.0` | HTTP host |
| `UVICORN_PORT` | `8000` | HTTP port |
| `UVICORN_WORKERS` | `1` | HTTP workers |
| `UVICORN_LOG_LEVEL` | `info` | HTTP log level |

Docker example:

```bash
docker build -t ddddocr-api .
docker run -d -p 8000:8000 ddddocr-api
```

### API

Each endpoint reads an uploaded image and passes its bytes directly to ddddocr.

#### Upload OCR

```bash
curl -X POST http://localhost:8000/ocr \
  -F 'file=@captcha.png'
```

#### Object Detection

```bash
curl -X POST http://localhost:8000/det \
  -F 'file=@target.png'
```

#### Slider Matching

```bash
curl -X POST http://localhost:8000/slide_match \
  -F 'target_image=@target.png' \
  -F 'background_image=@background.png'
```

The slider image comparison endpoint is `POST /slide_comparison`, with the same `target_image` and `background_image` fields.
