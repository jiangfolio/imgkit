"""统一业务错误与 JSON 响应。"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """对客户端可见的业务错误（不暴露内部细节）。"""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


async def unhandled_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error", "message": "处理失败，请稍后重试"},
    )