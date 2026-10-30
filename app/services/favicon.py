"""从上传图生成 Favicon 资源包（内存 ZIP）。"""

from __future__ import annotations

import json
import zipfile
from io import BytesIO

from PIL import Image

from app.services.image_io import open_image
from app.services.validate import ValidatedImage

# PNG 尺寸清单
_PNG_SIZES = (16, 32, 192, 512)
_ICO_SIZES = ((16, 16), (32, 32), (48, 48))
_APPLE_SIZE = 180


def _to_square(im: Image.Image, size: int) -> Image.Image:
    """居中 cover 裁切为正方形并缩放到 size。"""
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    cropped = im.crop((left, top, left + side, top + side))
    if cropped.mode == "P":
        cropped = cropped.convert("RGBA")
    return cropped.resize((size, size), Image.Resampling.LANCZOS)


def _png_bytes(im: Image.Image) -> bytes:
    buf = BytesIO()
    out = im if im.mode in ("RGB", "RGBA") else im.convert("RGBA")
    out.save(buf, format="PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def build_favicon_zip(validated: ValidatedImage) -> BytesIO:
    """
    1. 打开原图
    2. 生成各尺寸 PNG / ICO / apple-touch / manifest
    3. 写入内存 ZIP 并返回
    """
    # 1. 原图
    src = open_image(validated.data)

    # 2. 各尺寸
    square_512 = _to_square(src, 512)
    png_map: dict[int, Image.Image] = {512: square_512}
    for s in _PNG_SIZES:
        if s != 512:
            png_map[s] = square_512.resize((s, s), Image.Resampling.LANCZOS)

    apple = square_512.resize((_APPLE_SIZE, _APPLE_SIZE), Image.Resampling.LANCZOS)

    ico_buf = BytesIO()
    # Pillow 按 sizes 从源图生成多尺寸 ICO
    ico_src = square_512.convert("RGBA")
    ico_src.save(ico_buf, format="ICO", sizes=list(_ICO_SIZES))

    manifest = {
        "name": "App",
        "short_name": "App",
        "icons": [
            {"src": "/favicon-192x192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/favicon-512x512.png", "sizes": "512x512", "type": "image/png"},
        ],
        "theme_color": "#E07A3D",
        "background_color": "#F7F1E8",
        "display": "standalone",
    }

    # 3. 打包 ZIP
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("favicon.ico", ico_buf.getvalue())
        for s in _PNG_SIZES:
            zf.writestr(f"favicon-{s}x{s}.png", _png_bytes(png_map[s]))
        zf.writestr("apple-touch-icon.png", _png_bytes(apple))
        zf.writestr(
            "site.webmanifest",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        zf.writestr(
            "README.txt",
            "将 favicon.ico / PNG / apple-touch-icon 放到站点根目录，"
            "并在 HTML head 引用；site.webmanifest 可按需接入。\n",
        )
    zip_buf.seek(0)
    return zip_buf