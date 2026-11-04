"""二维码生成接口。"""

from fastapi import APIRouter, Form

from app.errors import AppError
from app.services.image_io import download_basename, file_response
from app.services.qrcode_gen import generate_qrcode
from app.services.validate import parse_output_format, parse_quality

router = APIRouter(tags=["qrcode"])


def _parse_int(raw: str, name: str, default: int, lo: int, hi: int) -> int:
    if raw is None or raw == "":
        return default
    try:
        v = int(raw)
    except (TypeError, ValueError):
        raise AppError("invalid_param", f"{name} 必须是整数") from None
    if v < lo or v > hi:
        raise AppError("invalid_param", f"{name} 须在 {lo}–{hi}")
    return v


@router.post("/qrcode")
async def qrcode_endpoint(
    content: str = Form(...),
    box_size: str = Form("10"),
    border: str = Form("2"),
    error_correction: str = Form("M"),
    format: str = Form("png"),
    quality: str = Form("90"),
):
    """根据文本生成二维码图片。"""
    # 1. 解析参数
    ec = (error_correction or "M").strip().upper()
    fmt = parse_output_format(format or "png", required=True)
    assert fmt is not None
    # 2. 生成并返回
    out, out_fmt = generate_qrcode(
        content,
        box_size=_parse_int(box_size, "box_size", 10, 2, 40),
        border=_parse_int(border, "border", 2, 0, 16),
        error_correction=ec,  # type: ignore[arg-type]
        format_name=fmt,
        quality=parse_quality(quality, default=90),
    )
    return file_response(out, out_fmt, download_basename(out_fmt, "qrcode"))
