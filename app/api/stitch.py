"""多图拼接接口。"""

from fastapi import APIRouter, File, Form, UploadFile

from app.config import settings
from app.errors import AppError
from app.middleware import read_upload_limited
from app.services.image_io import download_basename, file_response
from app.services.stitch import parse_hex_color, stitch_images
from app.services.validate import (
    ValidatedImage,
    parse_output_format,
    parse_quality,
    validate_upload_bytes,
)

router = APIRouter(tags=["stitch"])


def _parse_nonneg(raw: str, name: str, default: int = 0) -> int:
    if raw is None or raw == "":
        return default
    try:
        v = int(raw)
    except (TypeError, ValueError):
        raise AppError("invalid_param", f"{name} 必须是整数") from None
    if v < 0 or v > settings.max_margin:
        raise AppError("invalid_param", f"{name} 须在 0–{settings.max_margin}")
    return v


@router.post("/stitch")
async def stitch(
    files: list[UploadFile] = File(...),
    direction: str = Form("horizontal"),
    sort: str = Form("original"),
    margin: str = Form("0"),
    gap: str = Form("0"),
    align: str = Form("center"),
    bgcolor: str = Form("#ffffff"),
    format: str = Form("png"),
    quality: str = Form("90"),
):
    """
    多图拼接。multipart 字段名 files；可配置方向、排序、边距、间距、对齐与背景色。
    """
    # 1. 读入并校验每张图
    if not files:
        raise AppError("invalid_param", "请至少上传 2 张图")
    if len(files) > settings.max_stitch_files:
        raise AppError("invalid_param", f"最多拼接 {settings.max_stitch_files} 张图")

    items: list[tuple[str, ValidatedImage]] = []
    for f in files:
        data = await read_upload_limited(f)
        validated = validate_upload_bytes(data)
        name = f.filename or "image"
        items.append((name, validated))

    # 2. 解析参数
    direction_v = (direction or "horizontal").strip().lower()
    if direction_v not in ("horizontal", "vertical"):
        raise AppError("invalid_param", "direction 仅支持 horizontal / vertical")
    sort_v = (sort or "original").strip().lower()
    if sort_v not in ("original", "name_asc", "name_desc", "size_asc", "size_desc"):
        raise AppError("invalid_param", "sort 不支持")
    align_v = (align or "center").strip().lower()
    if align_v not in ("start", "center", "end"):
        raise AppError("invalid_param", "align 仅支持 start / center / end")
    fmt = parse_output_format(format or "png", required=True)
    assert fmt is not None

    # 3. 拼接并返回
    out, out_fmt = stitch_images(
        items,
        direction=direction_v,  # type: ignore[arg-type]
        sort=sort_v,  # type: ignore[arg-type]
        margin=_parse_nonneg(margin, "margin", 0),
        gap=_parse_nonneg(gap, "gap", 0),
        align=align_v,  # type: ignore[arg-type]
        bgcolor=parse_hex_color(bgcolor),
        format_name=fmt,
        quality=parse_quality(quality, default=90),
    )
    return file_response(out, out_fmt, download_basename(out_fmt, "stitched"))
