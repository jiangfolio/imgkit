"""缩放接口。"""

from fastapi import APIRouter, File, Form, UploadFile

from app.errors import AppError
from app.middleware import read_upload_limited
from app.services.image_io import download_basename, file_response
from app.services.resize import resize_process
from app.services.validate import (
    parse_optional_max_edge,
    parse_output_format,
    parse_quality,
    validate_upload_bytes,
)
from app.config import settings

router = APIRouter(tags=["resize"])


def _parse_positive_int(raw: str, name: str) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        v = int(raw)
    except (TypeError, ValueError):
        raise AppError("invalid_param", f"{name} 必须是整数") from None
    if v < 1 or v > settings.max_output_edge:
        raise AppError("invalid_param", f"{name} 须在 1–{settings.max_output_edge}")
    return v


@router.post("/resize")
async def resize(
    file: UploadFile = File(...),
    mode: str = Form("max_edge"),
    max_edge: str = Form(""),
    width: str = Form(""),
    height: str = Form(""),
    fit: str = Form("contain"),
    format: str = Form(""),
    quality: str = Form("85"),
):
    """按最长边或目标宽高缩放。"""
    data = await read_upload_limited(file)
    validated = validate_upload_bytes(data)

    mode_v = (mode or "max_edge").strip().lower()
    fit_v = (fit or "contain").strip().lower()
    if fit_v not in ("contain", "cover", "stretch"):
        raise AppError("invalid_param", "fit 仅支持 contain / cover / stretch")

    out, out_fmt = resize_process(
        validated,
        mode=mode_v,
        max_edge=parse_optional_max_edge(max_edge or None),
        width=_parse_positive_int(width, "width"),
        height=_parse_positive_int(height, "height"),
        fit=fit_v,  # type: ignore[arg-type]
        format_name=parse_output_format(format or None),
        quality=parse_quality(quality),
    )
    return file_response(out, out_fmt, download_basename(out_fmt, "resized"))