"""图像压缩（可选限边与转格式）。"""

from __future__ import annotations

from app.services.image_io import (
    encode_image,
    limit_max_edge,
    open_image,
    resolve_format,
)
from app.services.validate import ValidatedImage


def compress_image(
    validated: ValidatedImage,
    *,
    quality: int,
    format_name: str | None,
    max_edge: int | None,
    keep_exif: bool,
) -> tuple[bytes, str]:
    """
    1. 解码
    2. 可选最长边限制
    3. 按目标格式与质量编码
    """
    # 1. 解码
    im = open_image(validated.data)
    # 2. 限边
    im = limit_max_edge(im, max_edge)
    # 3. 编码
    fmt = resolve_format(format_name, validated.format_name)
    out = encode_image(im, fmt, quality=quality, keep_exif=keep_exif)
    return out, fmt