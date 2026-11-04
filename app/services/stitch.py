"""多图拼接（水平 / 垂直），全程内存。"""

from __future__ import annotations

from typing import Literal

from PIL import Image

from app.config import settings
from app.errors import AppError
from app.services.image_io import encode_image, open_image
from app.services.validate import ValidatedImage

Direction = Literal["horizontal", "vertical"]
SortMode = Literal["original", "name_asc", "name_desc", "size_asc", "size_desc"]
Align = Literal["start", "center", "end"]


def parse_hex_color(raw: str | None, default: tuple[int, int, int, int] = (255, 255, 255, 255)) -> tuple[int, int, int, int]:
    """解析 #RGB / #RRGGBB / #RRGGBBAA 为 RGBA。"""
    if raw is None or str(raw).strip() == "":
        return default
    s = str(raw).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) == 6:
        s += "ff"
    if len(s) != 8:
        raise AppError("invalid_param", "bgcolor 须为 #RGB / #RRGGBB / #RRGGBBAA")
    try:
        r, g, b, a = (int(s[i : i + 2], 16) for i in (0, 2, 4, 6))
    except ValueError as exc:
        raise AppError("invalid_param", "bgcolor 非法") from exc
    return (r, g, b, a)


def _sort_items(
    items: list[tuple[str, int, ValidatedImage]],
    sort: SortMode,
) -> list[tuple[str, int, ValidatedImage]]:
    if sort == "original":
        return items
    if sort == "name_asc":
        return sorted(items, key=lambda x: x[0].lower())
    if sort == "name_desc":
        return sorted(items, key=lambda x: x[0].lower(), reverse=True)
    if sort == "size_asc":
        return sorted(items, key=lambda x: x[1])
    if sort == "size_desc":
        return sorted(items, key=lambda x: x[1], reverse=True)
    raise AppError("invalid_param", "sort 不支持")


def _align_offset(total: int, piece: int, align: Align) -> int:
    if align == "start":
        return 0
    if align == "end":
        return max(0, total - piece)
    return max(0, (total - piece) // 2)


def stitch_images(
    items: list[tuple[str, ValidatedImage]],
    *,
    direction: Direction,
    sort: SortMode,
    margin: int,
    gap: int,
    align: Align,
    bgcolor: tuple[int, int, int, int],
    format_name: str,
    quality: int,
) -> tuple[bytes, str]:
    """
    1. 按 sort 重排文件
    2. 解码全部图像并统一为 RGBA
    3. 按方向计算画布尺寸（含边距与间距）
    4. 粘贴并编码
    """
    # 1. 校验数量与边距
    if len(items) < 2:
        raise AppError("invalid_param", "拼接至少需要 2 张图")
    if len(items) > settings.max_stitch_files:
        raise AppError(
            "invalid_param",
            f"最多拼接 {settings.max_stitch_files} 张图",
        )
    if margin < 0 or margin > settings.max_margin:
        raise AppError("invalid_param", f"margin 须在 0–{settings.max_margin}")
    if gap < 0 or gap > settings.max_margin:
        raise AppError("invalid_param", f"gap 须在 0–{settings.max_margin}")

    sized = [(name, len(v.data), v) for name, v in items]
    ordered = _sort_items(sized, sort)

    # 2. 解码
    images: list[Image.Image] = []
    for _, _, v in ordered:
        im = open_image(v.data)
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        images.append(im)

    # 3. 计算画布
    n = len(images)
    if direction == "horizontal":
        content_w = sum(im.width for im in images) + gap * (n - 1)
        content_h = max(im.height for im in images)
    else:
        content_w = max(im.width for im in images)
        content_h = sum(im.height for im in images) + gap * (n - 1)

    canvas_w = content_w + margin * 2
    canvas_h = content_h + margin * 2
    if canvas_w > settings.max_output_edge or canvas_h > settings.max_output_edge:
        raise AppError(
            "image_too_large",
            f"拼接结果边长不得超过 {settings.max_output_edge}",
        )
    if canvas_w * canvas_h > settings.max_pixels:
        raise AppError("image_too_large", "拼接结果像素过多，已拒绝处理")

    canvas = Image.new("RGBA", (canvas_w, canvas_h), bgcolor)

    # 4. 粘贴
    x = margin
    y = margin
    for im in images:
        if direction == "horizontal":
            oy = margin + _align_offset(content_h, im.height, align)
            canvas.paste(im, (x, oy), im)
            x += im.width + gap
        else:
            ox = margin + _align_offset(content_w, im.width, align)
            canvas.paste(im, (ox, y), im)
            y += im.height + gap

    fmt = format_name if format_name in ("webp", "jpeg", "png") else "png"
    out = encode_image(canvas, fmt, quality=quality, keep_exif=False)  # type: ignore[arg-type]
    return out, fmt
