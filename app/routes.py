from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from .config import Settings
from .images import ImageValidationError, decode_base64_image
from .schemas import (
    HealthResponse,
    InferenceResponse,
    OcrRequest,
    SlideComparisonRequest,
    SlideMatchRequest,
)
from .service import DdddOcrService, FeatureUnavailableError

router = APIRouter()


def get_service(request: Request) -> DdddOcrService:
    return request.app.state.ocr_service


ServiceDependency = Annotated[DdddOcrService, Depends(get_service)]


@contextmanager
def _translate_inference_errors():
    try:
        yield
    except FeatureUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc


async def _read_upload(
        upload: UploadFile,
        settings: Settings,
        field_name: str = "file",
) -> bytes:
    data = await upload.read(settings.max_image_bytes + 1)
    if not data:
        raise HTTPException(status_code=422, detail=f"{field_name} cannot be empty")
    if len(data) > settings.max_image_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"{field_name} exceeds the {settings.max_image_bytes} byte limit",
        )
    return data


def _parse_json_form(value: str | None, field_name: str) -> Any:
    if value is None or not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must contain valid JSON",
        ) from exc


@router.get("/", include_in_schema=False)
async def root(service: ServiceDependency) -> dict[str, Any]:
    return {
        "name": "DdddOcr API",
        "docs": "/docs",
        "features": service.features,
    }


@router.get("/health", response_model=HealthResponse, tags=["system"])
@router.get("/status", response_model=HealthResponse, include_in_schema=False)
async def health(service: ServiceDependency) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="1.0.0",
        features=service.features,
    )


@router.get("/config", tags=["system"])
async def config(service: ServiceDependency) -> dict[str, Any]:
    return service.settings.public_config()


@router.post("/ocr", response_model=InferenceResponse, tags=["OCR"])
async def ocr(
        payload: OcrRequest,
        service: ServiceDependency,
) -> InferenceResponse:
    try:
        image = decode_base64_image(payload.image, service.settings)
        with _translate_inference_errors():
            result, processing_time = await run_in_threadpool(
                service.classify,
                image,
                png_fix=payload.png_fix,
                probability=payload.probability,
                color_filter_colors=payload.color_filter_colors,
                color_filter_custom_ranges=payload.color_filter_custom_ranges,
            )
        return InferenceResponse(result=result, processing_time=processing_time)
    except ImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/ocr/file",
    response_model=InferenceResponse,
    tags=["OCR"],
)
@router.post("/upload/ocr", response_model=InferenceResponse, include_in_schema=False)
async def ocr_file(
        service: ServiceDependency,
        file: Annotated[UploadFile, File(description="Image file")],
        png_fix: Annotated[bool, Form()] = False,
        probability: Annotated[bool, Form()] = False,
        color_filter_colors: Annotated[str | None, Form()] = None,
        color_filter_custom_ranges: Annotated[str | None, Form()] = None,
) -> InferenceResponse:
    image = await _read_upload(file, service.settings)
    colors = _parse_json_form(color_filter_colors, "color_filter_colors")
    ranges = _parse_json_form(
        color_filter_custom_ranges, "color_filter_custom_ranges"
    )

    with _translate_inference_errors():
        result, processing_time = await run_in_threadpool(
            service.classify,
            image,
            png_fix=png_fix,
            probability=probability,
            color_filter_colors=colors,
            color_filter_custom_ranges=ranges,
        )
    return InferenceResponse(result=result, processing_time=processing_time)


@router.post("/det", response_model=InferenceResponse, tags=["Detection"])
@router.post("/detect", response_model=InferenceResponse, include_in_schema=False)
async def detect(
        payload: OcrRequest,
        service: ServiceDependency,
) -> InferenceResponse:
    try:
        image = decode_base64_image(payload.image, service.settings)
        with _translate_inference_errors():
            result, processing_time = await run_in_threadpool(service.detect, image)
        return InferenceResponse(result=result, processing_time=processing_time)
    except ImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/det/file", response_model=InferenceResponse, tags=["Detection"])
@router.post("/detect/file", response_model=InferenceResponse, include_in_schema=False)
async def detect_file(
        service: ServiceDependency,
        file: Annotated[UploadFile, File(description="Image file")],
) -> InferenceResponse:
    image = await _read_upload(file, service.settings)
    with _translate_inference_errors():
        result, processing_time = await run_in_threadpool(service.detect, image)
    return InferenceResponse(result=result, processing_time=processing_time)


@router.post(
    "/slide_match",
    response_model=InferenceResponse,
    tags=["Slider"],
)
@router.post(
    "/slide-match",
    response_model=InferenceResponse,
    include_in_schema=False,
)
async def slide_match(
        payload: SlideMatchRequest,
        service: ServiceDependency,
) -> InferenceResponse:
    try:
        target = decode_base64_image(
            payload.target_image, service.settings, "target_image"
        )
        background = decode_base64_image(
            payload.background_image, service.settings, "background_image"
        )
        with _translate_inference_errors():
            result, processing_time = await run_in_threadpool(
                service.slide_match,
                target,
                background,
                simple_target=payload.simple_target,
            )
        return InferenceResponse(result=result, processing_time=processing_time)
    except ImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/slide_match/file",
    response_model=InferenceResponse,
    tags=["Slider"],
)
@router.post(
    "/slide-match/file",
    response_model=InferenceResponse,
    include_in_schema=False,
)
async def slide_match_file(
        service: ServiceDependency,
        target_image: Annotated[UploadFile, File(description="Target image")],
        background_image: Annotated[UploadFile, File(description="Background image")],
        simple_target: Annotated[bool, Form()] = False,
) -> InferenceResponse:
    target = await _read_upload(target_image, service.settings, "target_image")
    background = await _read_upload(
        background_image, service.settings, "background_image"
    )
    with _translate_inference_errors():
        result, processing_time = await run_in_threadpool(
            service.slide_match,
            target,
            background,
            simple_target=simple_target,
        )
    return InferenceResponse(result=result, processing_time=processing_time)


@router.post(
    "/slide_comparison",
    response_model=InferenceResponse,
    tags=["Slider"],
)
@router.post(
    "/slide-comparison",
    response_model=InferenceResponse,
    include_in_schema=False,
)
async def slide_comparison(
        payload: SlideComparisonRequest,
        service: ServiceDependency,
) -> InferenceResponse:
    try:
        target = decode_base64_image(
            payload.target_image, service.settings, "target_image"
        )
        background = decode_base64_image(
            payload.background_image, service.settings, "background_image"
        )
        with _translate_inference_errors():
            result, processing_time = await run_in_threadpool(
                service.slide_comparison,
                target,
                background,
            )
        return InferenceResponse(result=result, processing_time=processing_time)
    except ImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/slide_comparison/file",
    response_model=InferenceResponse,
    tags=["Slider"],
)
@router.post(
    "/slide-comparison/file",
    response_model=InferenceResponse,
    include_in_schema=False,
)
async def slide_comparison_file(
        service: ServiceDependency,
        target_image: Annotated[UploadFile, File(description="Image containing the gap")],
        background_image: Annotated[UploadFile, File(description="Complete background")],
) -> InferenceResponse:
    target = await _read_upload(target_image, service.settings, "target_image")
    background = await _read_upload(
        background_image, service.settings, "background_image"
    )
    with _translate_inference_errors():
        result, processing_time = await run_in_threadpool(
            service.slide_comparison,
            target,
            background,
        )
    return InferenceResponse(result=result, processing_time=processing_time)
