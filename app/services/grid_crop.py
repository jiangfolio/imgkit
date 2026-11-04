"""九宫格（或自定义行列）裁剪，打包 ZIP。"""

from __future__ import annotations

import zipfile
from io import BytesIO

from app.config import settings
from app.errors import AppError
from app.services.image_io import encode_image, open_image
from app.services.validate import ValidatedImage


def crop_grid(
    validated: ValidatedImage,
    *,
    rows: int = 3,
    cols: int = 3,
    format_name: str = "png",
    quality: int = 90,
) -> BytesIO:
    """
    1. 校验行列
    2. 按等分网格裁切（余数像素分到右侧 / 下侧格子）
    3. 写入内存 ZIP
    """
    # 1. 校验
    if rows < settings.grid_min or rows > settings.grid_max:
        raise AppError(
            "invalid_param",
            f"rows 须在 {settings.grid_min}–{settings.grid_max}",
        )
    if cols < settings.grid_min or cols > settings.grid_max:
        raise AppError(
            "invalid_param",
            f"cols 须在 {settings.grid_min}–{settings.grid_max}",
        )

    im = open_image(validated.data)
    if im.mode == "P":
        im = im.convert("RGBA")

    w, h = im.size
    if w < cols or h < rows:
        raise AppError("invalid_param", "图像尺寸过小，无法按网格裁切")

    fmt = format_name if format_name in ("webp", "jpeg", "png") else "png"
    ext = {"webp": "webp", "jpeg": "jpg", "png": "png"}[fmt]

    # 2. 计算每格宽高（余数累加到最后一格）
    cell_w = w // cols
    cell_h = h // rows
    buf = BytesIO()

    # 3. 裁切并打包
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for r in range(rows):
            for c in range(cols):
                left = c * cell_w
                top = r * cell_h
                right = w if c == cols - 1 else (c + 1) * cell_w
                bottom = h if r == rows - 1 else (r + 1) * cell_h
                tile = im.crop((left, top, right, bottom))
                data = encode_image(tile, fmt, quality=quality, keep_exif=False)  # type: ignore[arg-type]
                name = f"grid_{r + 1}_{c + 1}.{ext}"
                zf.writestr(name, data)

    buf.seek(0)
    return buf
