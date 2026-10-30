"""安全响应头与按 IP 内存限流。"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.errors import AppError


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """为所有响应附加基础安全头。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' blob: data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    简单滑动窗口限流（进程内内存）。
    仅约束 /api/*，静态资源不计入。
    """

    def __init__(self, app, limit: int | None = None) -> None:
        super().__init__(app)
        self.limit = limit or settings.rate_limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_ip(self, request: Request) -> str:
        # 不信任 X-Forwarded-For（防伪造刷别人额度）；反代场景请在外层限流
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        ip = self._client_ip(request)
        now = time.monotonic()
        window = 60.0
        q = self._hits[ip]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= self.limit:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={"code": "rate_limited", "message": "请求过于频繁，请稍后再试"},
            )
        q.append(now)
        return await call_next(request)


async def read_upload_limited(upload) -> bytes:
    """
    流式读取上传，超过上限立即中断，避免一次吃满内存后再判。
    """
    from app.config import settings

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 256)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.max_upload_bytes:
            raise AppError(
                "file_too_large",
                f"文件过大，上限 {settings.max_upload_bytes // (1024 * 1024)}MB",
                status_code=413,
            )
        chunks.append(chunk)
    return b"".join(chunks)