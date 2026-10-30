"""Favicon 包生成接口。"""

from fastapi import APIRouter, File, UploadFile

from app.middleware import read_upload_limited
from app.services.favicon import build_favicon_zip
from app.services.image_io import zip_streaming_response
from app.services.validate import validate_upload_bytes

router = APIRouter(tags=["favicon"])


@router.post("/favicon")
async def favicon(file: UploadFile = File(...)):
    """上传任意图，返回 favicon 资源 ZIP。"""
    data = await read_upload_limited(file)
    validated = validate_upload_bytes(data)
    zip_buf = build_favicon_zip(validated)
    return zip_streaming_response(zip_buf, "favicon-pack.zip")