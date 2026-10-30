"""FastAPI 入口：API + 前端静态资源单进程托管。"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import compress, convert, favicon, resize
from app.errors import AppError, app_error_handler, unhandled_error_handler
from app.middleware import RateLimitMiddleware, SecurityHeadersMiddleware

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="imgkit",
    description="即时、无落盘图像处理（Favicon / 压缩 / 缩放 / 格式转换）",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(compress.router, prefix="/api")
app.include_router(resize.router, prefix="/api")
app.include_router(convert.router, prefix="/api")
app.include_router(favicon.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# 静态前端：构建产物位于 app/static
if STATIC_DIR.is_dir():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def index():
        index_file = STATIC_DIR / "index.html"
        if not index_file.is_file():
            return {"message": "前端未构建，请先执行 make build"}
        return FileResponse(index_file)

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        """SPA 回退；拒绝路径穿越，未知路径回 index。"""
        # 1. 拦截明显的穿越与敏感前缀
        if ".." in full_path or full_path.startswith("api/"):
            return FileResponse(STATIC_DIR / "index.html")
        # 2. 若静态文件存在则直出
        candidate = (STATIC_DIR / full_path).resolve()
        try:
            candidate.relative_to(STATIC_DIR.resolve())
        except ValueError:
            return FileResponse(STATIC_DIR / "index.html")
        if candidate.is_file():
            return FileResponse(candidate)
        # 3. 否则回前端入口
        return FileResponse(STATIC_DIR / "index.html")
