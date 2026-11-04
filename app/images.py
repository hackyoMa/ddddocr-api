from __future__ import annotations

import base64
import binascii
import io

from PIL import Image, UnidentifiedImageError

from .config import Settings

ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "JPG", "WEBP", "BMP", "GIF", "TIFF"}


class ImageValidationError(ValueError):
    """Raised when an uploaded or Base64 encoded image is invalid."""


def decode_base64_image(value: str, settings: Settings, field_name: str = "image") -> bytes:
    if not value or not value.strip():
        raise ImageValidationError(f"{field_name} cannot be empty")

    encoded = value.strip()
    if encoded.startswith("data:"):
        _, separator, encoded = encoded.partition(",")
        if not separator:
            raise ImageValidationError(f"{field_name} contains an invalid data URI")

    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ImageValidationError(f"{field_name} is not valid Base64") from exc

    validate_image(data, settings, field_name)
    return data


def validate_image(data: bytes, settings: Settings, field_name: str = "image") -> None:
    if not data:
        raise ImageValidationError(f"{field_name} cannot be empty")
    if len(data) > settings.max_image_bytes:
        raise ImageValidationError(
            f"{field_name} exceeds the {settings.max_image_bytes} byte limit"
        )

    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                formats = ", ".join(sorted(ALLOWED_IMAGE_FORMATS))
                raise ImageValidationError(
                    f"{field_name} has unsupported format {image.format!r}; "
                    f"supported formats: {formats}"
                )

            width, height = image.size
            if width > settings.max_image_side or height > settings.max_image_side:
                raise ImageValidationError(
                    f"{field_name} dimensions {width}x{height} exceed the "
                    f"{settings.max_image_side} pixel side limit"
                )

            image.verify()
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ImageValidationError(f"{field_name} is not a readable image") from exc
