"""二维码生成（内存）。"""

from __future__ import annotations

from io import BytesIO
from typing import Literal

import qrcode
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

from app.config import settings
from app.errors import AppError
from app.services.image_io import encode_image

ErrorLevel = Literal["L", "M", "Q", "H"]

_EC = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def generate_qrcode(
    content: str,
    *,
    box_size: int = 10,
    border: int = 2,
    error_correction: ErrorLevel = "M",
    format_name: str = "png",
    quality: int = 90,
) -> tuple[bytes, str]:
    """
    1. 校验内容与参数
    2. 用 qrcode 生成 PIL 图
    3. 编码为指定格式
    """
    # 1. 校验
    text = (content or "").strip()
    if not text:
        raise AppError("invalid_param", "内容不能为空")
    if len(text) > settings.max_qr_content_len:
        raise AppError(
            "invalid_param",
            f"内容过长，上限 {settings.max_qr_content_len} 字符",
        )
    if box_size < 2 or box_size > 40:
        raise AppError("invalid_param", "box_size 须在 2–40")
    if border < 0 or border > 16:
        raise AppError("invalid_param", "border 须在 0–16")
    ec = _EC.get(error_correction.upper() if error_correction else "M")
    if ec is None:
        raise AppError("invalid_param", "error_correction 仅支持 L / M / Q / H")

    # 2. 生成
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec,
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)
    im = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # 3. 编码
    fmt = format_name if format_name in ("webp", "jpeg", "png") else "png"
    if fmt == "png":
        buf = BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), fmt
    out = encode_image(im, fmt, quality=quality, keep_exif=False)  # type: ignore[arg-type]
    return out, fmt
