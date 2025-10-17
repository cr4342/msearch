"""
错误处理中间件
"""
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """自定义HTTP异常处理"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """验证异常处理"""
    logger.error(f"验证错误: {exc}")
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "请求参数验证失败", "details": exc.errors()}
    )


def add_error_handlers(app: FastAPI):
    """添加错误处理中间件"""
    app.add_exception_handler(StarletteHTTPException, custom_http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)