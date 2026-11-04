"""图像主色提取接口。"""

from fastapi import APIRouter, File, Form, UploadFile

from app.config import settings
from app.errors import AppError
from app.middleware import read_upload_limited
from app.services.colors import extract_colors
from app.services.validate import validate_upload_bytes

router = APIRouter(tags=["colors"])


@router.post("/colors")
async def colors(
    file: UploadFile = File(...),
    count: str = Form("6"),
):
    """提取图像主色，返回 JSON。"""
    # 1. 校验上传
    data = await read_upload_limited(file)
    validated = validate_upload_bytes(data)
    # 2. 解析色数
    try:
        n = int(count) if count not in (None, "") else 6
    except (TypeError, ValueError):
        raise AppError("invalid_param", "count 必须是整数") from None
    if n < settings.colors_min or n > settings.colors_max:
        raise AppError(
            "invalid_param",
            f"count 须在 {settings.colors_min}–{settings.colors_max}",
        )
    # 3. 提取
    palette = extract_colors(validated, count=n)
    return {"colors": palette}
