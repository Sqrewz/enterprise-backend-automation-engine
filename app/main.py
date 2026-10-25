from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api import router
from app.core.logging import configure_logging
from app.db import Base, engine

log = structlog.get_logger()

@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Enterprise Backend & Automation Engine", version="0.1.0", lifespan=lifespan)
app.include_router(router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(422, {"detail": "Validation failed", "errors": exc.errors()})

@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(500, {"detail": "Internal server error"})
