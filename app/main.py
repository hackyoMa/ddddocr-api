import threading
from contextlib import asynccontextmanager

from ddddocr import DdddOcr
from fastapi import FastAPI, File, UploadFile

from .config import get_ddddocr_options

inference_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ocr = DdddOcr(**get_ddddocr_options())
    yield


app = FastAPI(
    title="DdddOcr API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}


@app.post("/ocr")
def ocr(file: UploadFile = File(...)):
    with inference_lock:
        result = app.state.ocr.classification(file.file.read())
    return {"result": result}


@app.post("/det")
def det(file: UploadFile = File(...)):
    with inference_lock:
        result = app.state.ocr.detection(file.file.read())
    return {"result": result}


@app.post("/slide_match")
def slide_match(
        target_image: UploadFile = File(...),
        background_image: UploadFile = File(...),
):
    with inference_lock:
        result = app.state.ocr.slide_match(
            target_image.file.read(),
            background_image.file.read(),
        )
    return {"result": result}


@app.post("/slide_comparison")
def slide_comparison(
        target_image: UploadFile = File(...),
        background_image: UploadFile = File(...),
):
    with inference_lock:
        result = app.state.ocr.slide_comparison(
            target_image.file.read(),
            background_image.file.read(),
        )
    return {"result": result}
