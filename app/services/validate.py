"""上传字节校验：魔数、体积、像素上限。"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from app.config import settings
from app.errors import AppError

@dataclass(frozen=True)
class ValidatedImage:
    """通过校验的原始字节与检测格式。"""

    data: bytes
    format_name: str  # png | jpeg | webp


def detect_format(data: bytes) -> str:
    """
    仅依据文件头判定格式；拒绝 SVG 与未知类型。
    """
    if not data:
        raise AppError("empty_file", "文件为空")

    head = data[:64].lstrip()
    # 拒绝 SVG（文本魔数，可嵌入脚本）
    if head[:5].lower() == b"<?xml" or head[:4].lower() == b"<svg":
        raise AppError("unsupported_type", "不支持 SVG 格式")

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"

    raise AppError("unsupported_type", "仅支持 PNG / JPEG / WebP")


def validate_upload_bytes(data: bytes) -> ValidatedImage:
    """
    1. 检查体积上限
    2. 魔数识别格式
    3. 用 Pillow 打开并校验像素总数（防炸弹）
    """
    # 1. 体积
    if len(data) > settings.max_upload_bytes:
        raise AppError(
            "file_too_large",
            f"文件过大，上限 {settings.max_upload_bytes // (1024 * 1024)}MB",
            status_code=413,
        )

    # 2. 格式
    fmt = detect_format(data)

    # 3. 像素上限（先限制 Pillow 解压）
    Image.MAX_IMAGE_PIXELS = settings.max_pixels
    try:
        from io import BytesIO

        with Image.open(BytesIO(data)) as im:
            im.load()
            w, h = im.size
            if w <= 0 or h <= 0:
                raise AppError("invalid_image", "无效的图像尺寸")
            if w * h > settings.max_pixels:
                raise AppError("image_too_large", "图像像素过多，已拒绝处理")
    except AppError:
        raise
    except Image.DecompressionBombError:
        raise AppError("image_too_large", "图像像素过多，已拒绝处理") from None
    except Exception:
        raise AppError("invalid_image", "无法解析图像") from None

    return ValidatedImage(data=data, format_name=fmt)


def parse_quality(raw: str | int | None, default: int = 85) -> int:
    """解析并钳制 quality 到合法区间。"""
    if raw is None or raw == "":
        return default
    try:
        q = int(raw)
    except (TypeError, ValueError):
        raise AppError("invalid_param", "quality 必须是整数") from None
    if q < settings.quality_min or q > settings.quality_max:
        raise AppError(
            "invalid_param",
            f"quality 须在 {settings.quality_min}–{settings.quality_max}",
        )
    return q


def parse_optional_max_edge(raw: str | int | None) -> int | None:
    """可选最长边；空则不限制（仍受硬上限约束）。"""
    if raw is None or raw == "":
        return None
    try:
        v = int(raw)
    except (TypeError, ValueError):
        raise AppError("invalid_param", "max_edge 必须是整数") from None
    if v < 1 or v > settings.max_output_edge:
        raise AppError(
            "invalid_param",
            f"max_edge 须在 1–{settings.max_output_edge}",
        )
    return v


def parse_output_format(raw: str | None, *, required: bool = False) -> str | None:
    """输出格式：webp / jpeg / png。"""
    if raw is None or raw == "":
        if required:
            raise AppError("invalid_param", "format 为必填")
        return None
    fmt = raw.strip().lower()
    if fmt == "jpg":
        fmt = "jpeg"
    if fmt not in {"webp", "jpeg", "png"}:
        raise AppError("invalid_param", "format 仅支持 webp / jpeg / png")
    return fmt