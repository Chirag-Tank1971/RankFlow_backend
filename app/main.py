from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.ranking import router as ranking_router
from app.api.summary import router as summary_router
from app.api.transaction import router as transaction_router
from app.core.exceptions import AppException
from app.core.logging import get_logger, setup_logging
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.schemas.common import ErrorResponse

setup_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="RankFlow API",
        description="RankFlow — transaction processing and user ranking system",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(transaction_router)
    app.include_router(summary_router)
    app.include_router(ranking_router)

    register_exception_handlers(app)
    return app


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(message=exc.message).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Validation failure: %s", exc.errors())
        message = "Invalid request data"
        if exc.errors():
            first = exc.errors()[0]
            loc = first.get("loc", ())
            field = loc[-1] if loc else "field"
            detail = first.get("msg", message)
            message = f"{field}: {detail}"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(message=message).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(message=str(exc.detail)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(message="Internal server error").model_dump(),
        )


app = create_app()
