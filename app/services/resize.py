"""图像缩放。"""

from __future__ import annotations

from app.services.image_io import (
    FitMode,
    encode_image,
    open_image,
    resize_image,
    resolve_format,
)
from app.services.validate import ValidatedImage


def resize_process(
    validated: ValidatedImage,
    *,
    mode: str,
    max_edge: int | None,
    width: int | None,
    height: int | None,
    fit: FitMode,
    format_name: str | None,
    quality: int,
) -> tuple[bytes, str]:
    """
    1. 解码
    2. 按 mode/fit 缩放
    3. 编码输出
    """
    im = open_image(validated.data)
    im = resize_image(
        im,
        mode=mode,
        max_edge=max_edge,
        width=width,
        height=height,
        fit=fit,
    )
    fmt = resolve_format(format_name, validated.format_name)
    out = encode_image(im, fmt, quality=quality, keep_exif=False)
    return out, fmt