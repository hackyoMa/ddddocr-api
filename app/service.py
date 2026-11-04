from __future__ import annotations

import threading
import time
from collections.abc import Sequence
from typing import Any

from ddddocr import DdddOcr

from .config import Settings
from .images import validate_image


class FeatureUnavailableError(RuntimeError):
    """Raised when an endpoint is disabled by the process configuration."""


class DdddOcrService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._instance: DdddOcr | None = None
        self._inference_lock = threading.Lock()

    def initialize(self) -> None:
        if self._instance is None:
            self._instance = DdddOcr(**self.settings.ddddocr_kwargs())

    def close(self) -> None:
        self._instance = None

    @property
    def features(self) -> list[str]:
        features = ["slide"]
        if self._ocr_available:
            features.insert(0, "ocr")
        if self.settings.det:
            features.insert(0, "detection")
        return features

    @property
    def _ocr_available(self) -> bool:
        # ddddocr prioritizes detection when both ocr and det are true.
        return not self.settings.det and (
                self.settings.ocr or bool(self.settings.import_onnx_path)
        )

    def classify(
            self,
            image: bytes,
            *,
            png_fix: bool = False,
            probability: bool = False,
            color_filter_colors: Sequence[str] | None = None,
            color_filter_custom_ranges: Sequence[Sequence[Sequence[int]]] | None = None,
    ) -> tuple[Any, float]:
        if not self._ocr_available:
            raise FeatureUnavailableError(
                "OCR is disabled by DA_OCR/DA_DET configuration"
            )

        instance = self._ready_instance()
        validate_image(image, self.settings)

        started_at = time.perf_counter()
        with self._inference_lock:
            result = instance.classification(
                image,
                png_fix=png_fix,
                probability=probability,
                color_filter_colors=(
                    list(color_filter_colors) if color_filter_colors else None
                ),
                color_filter_custom_ranges=(
                    list(color_filter_custom_ranges)
                    if color_filter_custom_ranges
                    else None
                ),
            )
        return result, time.perf_counter() - started_at

    def detect(self, image: bytes) -> tuple[list[list[int]], float]:
        if not self.settings.det:
            raise FeatureUnavailableError(
                "target detection is disabled; set DA_DET=true to enable it"
            )

        instance = self._ready_instance()
        validate_image(image, self.settings)

        started_at = time.perf_counter()
        with self._inference_lock:
            result = instance.detection(image)
        return result, time.perf_counter() - started_at

    def slide_match(
            self,
            target_image: bytes,
            background_image: bytes,
            *,
            simple_target: bool = False,
    ) -> tuple[dict[str, Any], float]:
        instance = self._ready_instance()
        validate_image(target_image, self.settings, "target_image")
        validate_image(background_image, self.settings, "background_image")

        started_at = time.perf_counter()
        with self._inference_lock:
            result = instance.slide_match(
                target_image,
                background_image,
                simple_target=simple_target,
            )
        return result, time.perf_counter() - started_at

    def slide_comparison(
            self,
            target_image: bytes,
            background_image: bytes,
    ) -> tuple[dict[str, Any], float]:
        instance = self._ready_instance()
        validate_image(target_image, self.settings, "target_image")
        validate_image(background_image, self.settings, "background_image")

        started_at = time.perf_counter()
        with self._inference_lock:
            result = instance.slide_comparison(target_image, background_image)
        return result, time.perf_counter() - started_at

    def _ready_instance(self) -> DdddOcr:
        self.initialize()
        if self._instance is None:
            raise RuntimeError("DdddOcr instance is not initialized")
        return self._instance
