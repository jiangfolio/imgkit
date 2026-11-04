"""条形码生成（内存）。"""

from __future__ import annotations

from io import BytesIO

from barcode import get_barcode_class
from barcode.errors import BarcodeError
from barcode.writer import ImageWriter
from PIL import Image

from app.config import settings
from app.errors import AppError
from app.services.image_io import encode_image

# 对外暴露的类型 → python-barcode 类名
_SUPPORTED = {
    "code128": "code128",
    "code39": "code39",
    "ean13": "ean13",
    "ean8": "ean8",
    "upc": "upca",
    "isbn13": "isbn13",
}


def generate_barcode(
    content: str,
    *,
    barcode_type: str = "code128",
    write_text: bool = True,
    format_name: str = "png",
    quality: int = 90,
) -> tuple[bytes, str]:
    """
    1. 校验类型与内容
    2. 用 python-barcode 渲染为 PIL 图
    3. 编码输出
    """
    # 1. 校验
    text = (content or "").strip()
    if not text:
        raise AppError("invalid_param", "内容不能为空")
    if len(text) > settings.max_barcode_content_len:
        raise AppError(
            "invalid_param",
            f"内容过长，上限 {settings.max_barcode_content_len} 字符",
        )
    key = (barcode_type or "code128").strip().lower()
    class_name = _SUPPORTED.get(key)
    if class_name is None:
        raise AppError(
            "invalid_param",
            "barcode_type 仅支持 code128 / code39 / ean13 / ean8 / upc / isbn13",
        )

    # 2. 生成
    try:
        cls = get_barcode_class(class_name)
        writer = ImageWriter()
        options = {
            "module_width": 0.3,
            "module_height": 15.0,
            "quiet_zone": 2.0,
            "font_size": 10,
            "text_distance": 4.0,
            "write_text": write_text,
        }
        # add_checksum 等由具体类型决定；写入内存 BytesIO
        buf = BytesIO()
        instance = cls(text, writer=writer)
        instance.write(buf, options=options)
        buf.seek(0)
        im = Image.open(buf).convert("RGB")
    except BarcodeError as exc:
        raise AppError("invalid_param", f"条码内容不符合 {key} 规则") from exc
    except Exception:
        raise AppError("invalid_param", f"无法生成 {key} 条码，请检查内容") from None

    # 3. 编码
    fmt = format_name if format_name in ("webp", "jpeg", "png") else "png"
    out = encode_image(im, fmt, quality=quality, keep_exif=False)  # type: ignore[arg-type]
    return out, fmt
