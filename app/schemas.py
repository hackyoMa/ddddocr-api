from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Base64ImageRequest(BaseModel):
    image: str = Field(..., min_length=1, description="Base64 image, data URI accepted")


class OcrRequest(Base64ImageRequest):
    png_fix: bool = Field(False, description="Repair transparent PNG backgrounds")
    probability: bool = Field(False, description="Include per-character probabilities")
    color_filter_colors: list[str] | None = Field(
        None, description="Preset colors such as red, blue, or black"
    )
    color_filter_custom_ranges: list[list[list[int]]] | None = Field(
        None, description="Custom HSV ranges: [[[lower_hsv], [upper_hsv]]]"
    )


class SlideRequest(BaseModel):
    target_image: str = Field(..., min_length=1, description="Target image as Base64")
    background_image: str = Field(
        ..., min_length=1, description="Background image as Base64"
    )


class SlideMatchRequest(SlideRequest):
    simple_target: bool = Field(False, description="Use the simple template matcher")


class SlideComparisonRequest(SlideRequest):
    """Two images with identical dimensions used for gap comparison."""


class InferenceResponse(BaseModel):
    result: Any
    processing_time: float = Field(..., description="Processing time in seconds")


class HealthResponse(BaseModel):
    status: str
    version: str
    features: list[str]
