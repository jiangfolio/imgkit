"""从图像中提取主色。"""

from __future__ import annotations

from PIL import Image

from app.config import settings
from app.errors import AppError
from app.services.image_io import open_image
from app.services.validate import ValidatedImage


def extract_colors(validated: ValidatedImage, *, count: int = 6) -> list[dict]:
    """
    1. 校验色数
    2. 缩小图后中位切分量化，统计像素占比
    3. 按占比降序返回 hex / rgb / ratio
    """
    # 1. 校验
    if count < settings.colors_min or count > settings.colors_max:
        raise AppError(
            "invalid_param",
            f"count 须在 {settings.colors_min}–{settings.colors_max}",
        )

    # 2. 缩小 + 量化（加速且抑制噪点）
    im = open_image(validated.data).convert("RGB")
    im.thumbnail((160, 160))
    # 多取一点再合并相近色，避免量化不足
    quantized = im.quantize(
        colors=min(64, max(count * 4, count)),
        method=Image.Quantize.MEDIANCUT,
    )
    palette = quantized.getpalette() or []
    raw_counts = quantized.getcolors() or []

    # 统计 RGB → 像素数
    totals: dict[tuple[int, int, int], int] = {}
    for pixels, idx in raw_counts:
        if idx * 3 + 2 >= len(palette):
            continue
        rgb = (palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2])
        totals[rgb] = totals.get(rgb, 0) + pixels

    if not totals:
        raise AppError("invalid_image", "无法提取颜色")

    # 3. 按占比排序，取前 count
    total_px = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:count]
    result: list[dict] = []
    for (r, g, b), n in ranked:
        result.append(
            {
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "rgb": [r, g, b],
                "ratio": round(n / total_px, 4),
            }
        )
    return result
