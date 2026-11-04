import os


def get_ddddocr_options() -> dict:
    def env_bool(name: str, default: bool) -> bool:
        value = os.getenv(name)
        return default if value is None else value.lower() == "true"

    return {
        "ocr": env_bool("DA_OCR", True),
        "det": env_bool("DA_DET", False),
        "old": env_bool("DA_OLD", False),
        "beta": env_bool("DA_BETA", False),
        "use_gpu": env_bool("DA_USE_GPU", False),
        "device_id": int(os.getenv("DA_DEVICE_ID", "0")),
        "show_ad": env_bool("DA_SHOW_AD", False),
        "import_onnx_path": os.getenv("DA_IMPORT_ONNX_PATH", ""),
        "charsets_path": os.getenv("DA_CHARSETS_PATH", ""),
    }
