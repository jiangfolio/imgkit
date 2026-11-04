"""条形码生成接口。"""

from fastapi import APIRouter, Form

from app.services.barcode_gen import generate_barcode
from app.services.image_io import download_basename, file_response
from app.services.validate import parse_output_format, parse_quality

router = APIRouter(tags=["barcode"])


@router.post("/barcode")
async def barcode_endpoint(
    content: str = Form(...),
    barcode_type: str = Form("code128"),
    write_text: str = Form("true"),
    format: str = Form("png"),
    quality: str = Form("90"),
):
    """根据文本生成条形码图片。"""
    # 1. 解析参数
    fmt = parse_output_format(format or "png", required=True)
    assert fmt is not None
    show_text = str(write_text).lower() in ("1", "true", "yes", "on")
    # 2. 生成并返回
    out, out_fmt = generate_barcode(
        content,
        barcode_type=barcode_type,
        write_text=show_text,
        format_name=fmt,
        quality=parse_quality(quality, default=90),
    )
    return file_response(out, out_fmt, download_basename(out_fmt, "barcode"))
