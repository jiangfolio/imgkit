"""压缩接口。"""

from fastapi import APIRouter, File, Form, UploadFile

from app.middleware import read_upload_limited
from app.services.compress import compress_image
from app.services.image_io import download_basename, file_response
from app.services.validate import (
    parse_optional_max_edge,
    parse_output_format,
    parse_quality,
    validate_upload_bytes,
)

router = APIRouter(tags=["compress"])


@router.post("/compress")
async def compress(
    file: UploadFile = File(...),
    quality: str = Form("85"),
    format: str = Form(""),
    max_edge: str = Form(""),
    keep_exif: str = Form("false"),
):
    """
    压缩图像；可选转格式与最长边限制。
    """
    # 1. 校验上传
    data = await read_upload_limited(file)
    validated = validate_upload_bytes(data)
    # 2. 解析参数
    q = parse_quality(quality)
    fmt = parse_output_format(format or None)
    edge = parse_optional_max_edge(max_edge or None)
    keep = str(keep_exif).lower() in ("1", "true", "yes", "on")
    # 3. 处理并返回
    out, out_fmt = compress_image(
        validated,
        quality=q,
        format_name=fmt,
        max_edge=edge,
        keep_exif=keep,
    )
    return file_response(out, out_fmt, download_basename(out_fmt, "compressed"))