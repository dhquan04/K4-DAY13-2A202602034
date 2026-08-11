from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .dashboard import build_dashboard_html
from .exception_handlers import register_exception_handlers
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import record_received, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .tracing import tracing_enabled

configure_logging()
log = get_logger()
app = FastAPI(title="Day 13 Observability Lab")
app.add_middleware(CorrelationIdMiddleware)
register_exception_handlers(app)
agent = LabAgent()


@app.on_event("startup")
async def startup() -> None:
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "day13-observability-lab"),
        env=os.getenv("APP_ENV", "dev"),
        payload={"tracing_enabled": tracing_enabled()},
    )


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "tracing_enabled": tracing_enabled(), "incidents": status()}


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(build_dashboard_html())


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    bind_contextvars(
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id,
        feature=body.feature,
        model=agent.model,
        env=os.getenv("APP_ENV", "dev"),
    )
    # Available to the centralized exception handler without echoing raw user text.
    request.state.message_preview = summarize_text(body.message)

    log.info(
        "request_received",
        service="api",
        payload={"message_preview": request.state.message_preview},
    )
    record_received()
    result = agent.run(
        user_id=body.user_id,
        feature=body.feature,
        session_id=body.session_id,
        message=body.message,
    )
    log.info(
        "response_sent",
        service="api",
        latency_ms=result.latency_ms,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_usd=result.cost_usd,
        quality_score=result.quality_score,
        payload={"answer_preview": summarize_text(result.answer)},
    )
    return ChatResponse(
        answer=result.answer,
        correlation_id=request.state.correlation_id,
        latency_ms=result.latency_ms,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_usd=result.cost_usd,
        quality_score=result.quality_score,
    )


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
