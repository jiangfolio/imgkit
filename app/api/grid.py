"""九宫格 / 网格裁剪接口。"""

from fastapi import APIRouter, File, Form, UploadFile

from app.config import settings
from app.errors import AppError
from app.middleware import read_upload_limited
from app.services.grid_crop import crop_grid
from app.services.image_io import zip_streaming_response
from app.services.validate import parse_output_format, parse_quality, validate_upload_bytes

router = APIRouter(tags=["grid"])


def _parse_grid(raw: str, name: str, default: int) -> int:
    if raw is None or raw == "":
        return default
    try:
        v = int(raw)
    except (TypeError, ValueError):
        raise AppError("invalid_param", f"{name} 必须是整数") from None
    if v < settings.grid_min or v > settings.grid_max:
        raise AppError(
            "invalid_param",
            f"{name} 须在 {settings.grid_min}–{settings.grid_max}",
        )
    return v


@router.post("/grid")
async def grid(
    file: UploadFile = File(...),
    rows: str = Form("3"),
    cols: str = Form("3"),
    format: str = Form("png"),
    quality: str = Form("90"),
):
    """按网格裁切图像，返回 ZIP。"""
    # 1. 校验上传
    data = await read_upload_limited(file)
    validated = validate_upload_bytes(data)
    # 2. 解析参数
    fmt = parse_output_format(format or "png", required=True)
    assert fmt is not None
    r = _parse_grid(rows, "rows", 3)
    c = _parse_grid(cols, "cols", 3)
    # 3. 裁切打包
    zip_buf = crop_grid(
        validated,
        rows=r,
        cols=c,
        format_name=fmt,
        quality=parse_quality(quality, default=90),
    )
    return zip_streaming_response(zip_buf, "grid-pack.zip")
