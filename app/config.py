from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Mapping

_SIZE_PATTERN = re.compile(r"^(?P<value>\d+)\s*(?P<unit>B|KB|MB|GB)?$", re.IGNORECASE)
_SIZE_MULTIPLIERS = {
    "": 1,
    "B": 1,
    "KB": 1024,
    "MB": 1024 ** 2,
    "GB": 1024 ** 3,
}
_TRUE_VALUES = {"1", "true", "yes", "on", "y"}
_FALSE_VALUES = {"0", "false", "no", "off", "n"}


class ConfigurationError(ValueError):
    """Raised when a service environment variable is invalid."""


def _parse_bool(name: str, value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ConfigurationError(
        f"{name} must be a boolean (true/false, 1/0, yes/no), got {value!r}"
    )


def _parse_non_negative_int(name: str, value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer, got {value!r}") from exc
    if parsed < 0:
        raise ConfigurationError(f"{name} must be greater than or equal to 0")
    return parsed


def _parse_positive_int(name: str, value: str) -> int:
    parsed = _parse_non_negative_int(name, value)
    if parsed == 0:
        raise ConfigurationError(f"{name} must be greater than 0")
    return parsed


def _parse_size(name: str, value: str) -> int:
    match = _SIZE_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ConfigurationError(
            f"{name} must be a byte count with an optional B, KB, MB, or GB suffix, "
            f"got {value!r}"
        )

    size = int(match.group("value")) * _SIZE_MULTIPLIERS[
        (match.group("unit") or "").upper()
    ]
    if size <= 0:
        raise ConfigurationError(f"{name} must be greater than 0")
    return size


@dataclass(frozen=True, slots=True)
class Settings:
    ocr: bool = True
    det: bool = False
    old: bool = False
    beta: bool = False
    use_gpu: bool = False
    device_id: int = 0
    show_ad: bool = True
    import_onnx_path: str = ""
    charsets_path: str = ""
    max_image_bytes: int = 8 * 1024 * 1024
    max_image_side: int = 4096

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if environ is None else environ

        def get(name: str, default: str) -> str:
            value = env.get(name)
            if value is None or not value.strip():
                return default
            return value

        settings = cls(
            ocr=_parse_bool("DA_OCR", get("DA_OCR", "true")),
            det=_parse_bool("DA_DET", get("DA_DET", "false")),
            old=_parse_bool("DA_OLD", get("DA_OLD", "false")),
            beta=_parse_bool("DA_BETA", get("DA_BETA", "false")),
            use_gpu=_parse_bool("DA_USE_GPU", get("DA_USE_GPU", "false")),
            device_id=_parse_non_negative_int(
                "DA_DEVICE_ID", get("DA_DEVICE_ID", "0")
            ),
            show_ad=_parse_bool("DA_SHOW_AD", get("DA_SHOW_AD", "true")),
            import_onnx_path=get("DA_IMPORT_ONNX_PATH", "").strip(),
            charsets_path=get("DA_CHARSETS_PATH", "").strip(),
            max_image_bytes=_parse_size(
                "DA_MAX_IMAGE_BYTES", get("DA_MAX_IMAGE_BYTES", "8MB")
            ),
            max_image_side=_parse_positive_int(
                "DA_MAX_IMAGE_SIDE", get("DA_MAX_IMAGE_SIDE", "4096")
            ),
        )

        if settings.old and settings.beta:
            raise ConfigurationError("DA_OLD and DA_BETA cannot both be true")

        return settings

    def ddddocr_kwargs(self) -> dict[str, Any]:
        """Return the exact configuration accepted by ``DdddOcr``."""
        return {
            "ocr": self.ocr,
            "det": self.det,
            "old": self.old,
            "beta": self.beta,
            "use_gpu": self.use_gpu,
            "device_id": self.device_id,
            "show_ad": self.show_ad,
            "import_onnx_path": self.import_onnx_path,
            "charsets_path": self.charsets_path,
        }

    def public_config(self) -> dict[str, Any]:
        return {
            **self.ddddocr_kwargs(),
            "max_image_bytes": self.max_image_bytes,
            "max_image_side": self.max_image_side,
        }
