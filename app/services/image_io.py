"""图像解码、缩放辅助、编码与响应构造（全程内存）。"""

from __future__ import annotations

from io import BytesIO
from typing import Literal
from urllib.parse import quote

from PIL import Image, ImageOps
from fastapi.responses import Response, StreamingResponse

from app.config import settings
from app.errors import AppError

OutputFormat = Literal["webp", "jpeg", "png"]
FitMode = Literal["contain", "cover", "stretch"]

_CONTENT_TYPES: dict[str, str] = {
    "webp": "image/webp",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "zip": "application/zip",
}

_EXT: dict[str, str] = {
    "webp": "webp",
    "jpeg": "jpg",
    "png": "png",
}


def open_image(data: bytes) -> Image.Image:
    """打开图像并应用 EXIF 方向，返回独立副本。"""
    Image.MAX_IMAGE_PIXELS = settings.max_pixels
    im = Image.open(BytesIO(data))
    im = ImageOps.exif_transpose(im)
    return im.copy()


def drop_exif(im: Image.Image) -> Image.Image:
    """剥离 EXIF/附加信息，编码时不写入元数据。"""
    clean = im.copy()
    clean.info = {}
    return clean


def ensure_rgb_for_jpeg(im: Image.Image) -> Image.Image:
    """JPEG 不支持透明：RGBA/P 等铺白底转 RGB。"""
    if im.mode in ("RGB", "L"):
        return im.convert("RGB") if im.mode == "L" else im
    if im.mode == "RGBA":
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[3])
        return bg
    if im.mode == "P":
        if "transparency" in im.info:
            im = im.convert("RGBA")
            return ensure_rgb_for_jpeg(im)
        return im.convert("RGB")
    return im.convert("RGB")


def limit_max_edge(im: Image.Image, max_edge: int | None) -> Image.Image:
    """最长边超出则等比缩小。"""
    if max_edge is None:
        return im
    w, h = im.size
    longest = max(w, h)
    if longest <= max_edge:
        return im
    scale = max_edge / longest
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def resize_image(
    im: Image.Image,
    *,
    mode: str,
    max_edge: int | None,
    width: int | None,
    height: int | None,
    fit: FitMode,
) -> Image.Image:
    """
    按 mode/fit 缩放。
    - max_edge：等比限制最长边
    - width_height：按 fit 处理目标宽高
    """
    if mode == "max_edge":
        if max_edge is None:
            raise AppError("invalid_param", "mode=max_edge 时需要 max_edge")
        return limit_max_edge(im, max_edge)

    if mode != "width_height":
        raise AppError("invalid_param", "mode 仅支持 max_edge / width_height")

    if width is None or height is None or width < 1 or height < 1:
        raise AppError("invalid_param", "width_height 模式需要正整数 width/height")
    if width > settings.max_output_edge or height > settings.max_output_edge:
        raise AppError(
            "invalid_param",
            f"宽高不得超过 {settings.max_output_edge}",
        )

    if fit == "stretch":
        return im.resize((width, height), Image.Resampling.LANCZOS)

    if fit == "contain":
        fitted = ImageOps.contain(im, (width, height), Image.Resampling.LANCZOS)
        # 居中贴到目标画布（透明或白底）
        canvas_mode = "RGBA" if fitted.mode in ("RGBA", "LA", "P") else "RGB"
        if canvas_mode == "RGBA":
            canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            if fitted.mode != "RGBA":
                fitted = fitted.convert("RGBA")
        else:
            canvas = Image.new("RGB", (width, height), (255, 255, 255))
            fitted = fitted.convert("RGB")
        ox = (width - fitted.width) // 2
        oy = (height - fitted.height) // 2
        canvas.paste(fitted, (ox, oy))
        return canvas

    if fit == "cover":
        return ImageOps.fit(im, (width, height), Image.Resampling.LANCZOS, centering=(0.5, 0.5))

    raise AppError("invalid_param", "fit 仅支持 contain / cover / stretch")


def encode_image(
    im: Image.Image,
    fmt: OutputFormat,
    *,
    quality: int = 85,
    keep_exif: bool = False,
) -> bytes:
    """编码为指定格式字节。"""
    if not keep_exif:
        im = drop_exif(im)

    buf = BytesIO()
    if fmt == "jpeg":
        im = ensure_rgb_for_jpeg(im)
        im.save(buf, format="JPEG", quality=quality, optimize=True)
    elif fmt == "webp":
        # WebP 可带透明
        if im.mode == "P":
            im = im.convert("RGBA")
        im.save(buf, format="WEBP", quality=quality, method=6)
    elif fmt == "png":
        if im.mode == "P":
            im = im.convert("RGBA")
        # quality 映射到 compress_level 0–9（质量越高压缩越轻）
        level = max(0, min(9, round((100 - quality) / 100 * 9)))
        im.save(buf, format="PNG", optimize=True, compress_level=level)
    else:
        raise AppError("invalid_param", "不支持的输出格式")
    return buf.getvalue()


def resolve_format(requested: str | None, source_format: str) -> OutputFormat:
    """未指定输出格式时沿用源格式。"""
    if requested:
        return requested  # type: ignore[return-value]
    if source_format in ("webp", "jpeg", "png"):
        return source_format  # type: ignore[return-value]
    return "png"


def file_response(data: bytes, fmt: str, download_name: str) -> Response:
    """构造带 Content-Disposition 的下载响应。"""
    media = _CONTENT_TYPES.get(fmt, "application/octet-stream")
    # 仅 ASCII 文件名 + RFC5987 回退，避免注入
    safe_ascii = "".join(c if c.isascii() and c.isalnum() or c in "._-" else "_" for c in download_name)
    if not safe_ascii:
        safe_ascii = "download"
    encoded = quote(download_name)
    headers = {
        "Content-Disposition": (
            f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{encoded}"
        ),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(content=data, media_type=media, headers=headers)


def zip_streaming_response(buf: BytesIO, download_name: str = "favicon-pack.zip") -> StreamingResponse:
    """ZIP 内存流响应。"""
    buf.seek(0)
    safe_ascii = "favicon-pack.zip"
    encoded = quote(download_name)
    headers = {
        "Content-Disposition": (
            f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{encoded}"
        ),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    return StreamingResponse(buf, media_type="application/zip", headers=headers)


def download_basename(fmt: OutputFormat, prefix: str = "imgkit") -> str:
    return f"{prefix}.{_EXT[fmt]}"