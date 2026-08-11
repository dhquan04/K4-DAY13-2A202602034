from __future__ import annotations

import re
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logging_config import get_logger
from .metrics import record_error
from .pii import scrub_text

log = get_logger()

_SAFE_ERROR_TYPE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]{0,63}$")


def safe_error_type(exc: BaseException | str) -> str:
    """Keep only a class-name-like token so metrics never store raw exception text/PII."""
    name = type(exc).__name__ if isinstance(exc, BaseException) else str(exc)
    if _SAFE_ERROR_TYPE.match(name):
        return name
    match = re.match(r"[A-Za-z_][A-Za-z0-9_.]*", name)
    return match.group(0)[:64] if match else "UnknownError"


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _error_body(
    *,
    status_code: int,
    error_type: str,
    detail: str,
    correlation_id: str | None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status_code": status_code,
        "error_type": error_type,
        "detail": scrub_text(detail),
        "correlation_id": correlation_id,
    }


def _log_request_failed(
    request: Request,
    *,
    error_type: str,
    detail: str,
    exc: BaseException | None = None,
) -> None:
    payload: dict[str, Any] = {"detail": scrub_text(detail)}
    message_preview = getattr(request.state, "message_preview", None)
    if message_preview:
        payload["message_preview"] = message_preview

    log_kwargs: dict[str, Any] = {
        "service": "api",
        "error_type": error_type,
        "payload": payload,
    }
    if exc is not None:
        log.error("request_failed", exc_info=exc, **log_kwargs)
    else:
        log.error("request_failed", **log_kwargs)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    error_type = "RequestValidationError"
    # Do not echo raw request body / input values (may contain PII).
    detail = "Request validation failed"
    body = _error_body(
        status_code=422,
        error_type=error_type,
        detail=detail,
        correlation_id=_correlation_id(request),
    )
    return JSONResponse(status_code=422, content=body)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    error_type = safe_error_type("HTTPException")
    raw_detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    # Prefer short class-like tokens already passed as detail (e.g. from older paths).
    if _SAFE_ERROR_TYPE.match(raw_detail):
        error_type = raw_detail
        client_detail = raw_detail
    else:
        client_detail = scrub_text(raw_detail)

    if exc.status_code >= 500:
        record_error(error_type)
        _log_request_failed(request, error_type=error_type, detail=raw_detail)

    body = _error_body(
        status_code=exc.status_code,
        error_type=error_type,
        detail=client_detail if exc.status_code < 500 else "Internal server error",
        correlation_id=_correlation_id(request),
    )
    return JSONResponse(status_code=exc.status_code, content=body)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_type = safe_error_type(exc)
    record_error(error_type)
    _log_request_failed(
        request,
        error_type=error_type,
        detail=str(exc),
        exc=exc,
    )
    body = _error_body(
        status_code=500,
        error_type=error_type,
        detail="Internal server error",
        correlation_id=_correlation_id(request),
    )
    return JSONResponse(status_code=500, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
