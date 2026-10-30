"""格式转换接口。"""

from fastapi import APIRouter, File, Form, UploadFile

from app.middleware import read_upload_limited
from app.services.convert import convert_image
from app.services.image_io import download_basename, file_response
from app.services.validate import (
    parse_optional_max_edge,
    parse_output_format,
    parse_quality,
    validate_upload_bytes,
)

router = APIRouter(tags=["convert"])


@router.post("/convert")
async def convert(
    file: UploadFile = File(...),
    format: str = Form(...),
    quality: str = Form("85"),
    max_edge: str = Form(""),
):
    """转换为 WebP / JPEG / PNG。"""
    data = await read_upload_limited(file)
    validated = validate_upload_bytes(data)
    fmt = parse_output_format(format, required=True)
    assert fmt is not None
    out, out_fmt = convert_image(
        validated,
        format_name=fmt,
        quality=parse_quality(quality),
        max_edge=parse_optional_max_edge(max_edge or None),
    )
    return file_response(out, out_fmt, download_basename(out_fmt, "converted"))