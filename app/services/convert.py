"""格式转换（可选先限边）。"""

from __future__ import annotations

from app.services.image_io import encode_image, limit_max_edge, open_image
from app.services.validate import ValidatedImage


def convert_image(
    validated: ValidatedImage,
    *,
    format_name: str,
    quality: int,
    max_edge: int | None,
) -> tuple[bytes, str]:
    """
    1. 解码
    2. 可选限边
    3. 转到目标格式
    """
    im = open_image(validated.data)
    im = limit_max_edge(im, max_edge)
    out = encode_image(im, format_name, quality=quality, keep_exif=False)  # type: ignore[arg-type]
    return out, format_name