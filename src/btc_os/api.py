import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.trustedhost import TrustedHostMiddleware

from btc_os import __version__
from btc_os.config import Settings
from btc_os.domain import TargetRequest, now
from btc_os.engine import TradingEngine
from btc_os.feed import MarketFeed
from btc_os.observability import RUN_ID, configure_logs
from btc_os.risk import RiskRejected
from btc_os.storage import PostgresStore, Store


class Controls(BaseModel):
    kill_switch: bool | None = None
    strategy_enabled: bool | None = None


def create_app(
    settings: Settings | None = None, store: Store | None = None, start_feed: bool = True
) -> FastAPI:
    config = settings or Settings()
    storage = store or PostgresStore(config.database_url.get_secret_value())
    engine = TradingEngine(config, storage)
    feed = MarketFeed(engine)
    log = configure_logs(config.data_root)
    started = now()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine.start()
        log.info("startup_reconciliation_complete" if engine.reconciled else "startup_blocked")
        task = asyncio.create_task(feed.run()) if start_feed else None
        yield
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        log.info("shutdown")
        if isinstance(storage, PostgresStore):
            storage.close()

    app = FastAPI(title="BTC Quant OS PAPER", version=__version__, lifespan=lifespan)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )
    app.state.engine, app.state.feed = engine, feed

    @app.exception_handler(RiskRejected)
    async def rejected(request: Request, exc: RiskRejected) -> JSONResponse:
        log.warning("risk_rejected")
        return JSONResponse(
            {"detail": str(exc), "environment_id": "INTERNAL_PAPER"}, status_code=409
        )

    async def write_guard(
        request: Request, x_btc_os: Annotated[str | None, Header()] = None
    ) -> None:
        origin = request.headers.get("origin")
        if x_btc_os != "paper-terminal" or (
            origin
            and origin not in {f"http://127.0.0.1:{config.port}", f"http://localhost:{config.port}"}
        ):
            raise HTTPException(403, "Local PAPER terminal header/origin required")

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {
            "version": __version__,
            "run_id": RUN_ID,
            "environment_id": "INTERNAL_PAPER",
            "live_enabled": False,
            "database": engine.persistence_ok,
            "reconciled": engine.reconciled,
            "uptime_seconds": (now() - started).total_seconds(),
            "risk_flags": engine.snapshot()["risk_flags"],
            "feed": feed.metrics,
            "feed_message": feed.message,
        }

    @app.get("/api/state")
    async def state() -> dict[str, Any]:
        return {**engine.snapshot(), "system": await health()}

    @app.post("/api/paper/target")
    async def target(
        body: TargetRequest, request: Request, x_btc_os: Annotated[str | None, Header()] = None
    ) -> dict[str, Any]:
        await write_guard(request, x_btc_os)
        orders = await engine.target(body)
        log.info(
            "paper_target_committed",
            extra={
                "decision_id": orders[0].decision_id if orders else None,
                "correlation_id": body.client_id,
            },
        )
        return {
            "environment_id": "INTERNAL_PAPER",
            "orders": [o.model_dump(mode="json") for o in orders],
        }

    @app.post("/api/paper/controls")
    async def controls(
        body: Controls, request: Request, x_btc_os: Annotated[str | None, Header()] = None
    ) -> dict[str, Any]:
        await write_guard(request, x_btc_os)
        await engine.controls(body.kill_switch, body.strategy_enabled)
        log.info("paper_controls_committed")
        return engine.snapshot()

    @app.websocket("/ws")
    async def stream(socket: WebSocket) -> None:
        origin = socket.headers.get("origin")
        if origin and origin not in {
            f"http://127.0.0.1:{config.port}",
            f"http://localhost:{config.port}",
        }:
            await socket.close(code=1008)
            return
        await socket.accept()
        try:
            while True:
                await socket.send_json({**engine.snapshot(), "system": await health()})
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            return

    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if dist.is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(
                dist / "index.html",
                headers={
                    "Cache-Control": "no-cache",
                    "Content-Security-Policy": "default-src 'self'; connect-src 'self' ws://127.0.0.1:* ws://localhost:*; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'",
                },
            )

    return app
