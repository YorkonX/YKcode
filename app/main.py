import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .models import Position, PositionSnapshot, TradeLogEntry
from .okx import OkxClient, load_client_from_env
from .storage import append_trade_log, setup_logging, write_positions_to_excel

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
LOG_PATH = Path(os.environ.get("TRADE_LOG_PATH", DATA_DIR / "logs" / "trade_journal.log"))
EXCEL_PATH = Path(os.environ.get("EXCEL_PATH", DATA_DIR / "positions.xlsx"))
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "15"))
INST_TYPE = os.environ.get("OKX_INST_TYPE", "SWAP")

app = FastAPI(title="OKX Position Tracker", version="0.1.0")
app.mount("/static", StaticFiles(directory="frontend", html=True), name="static")


async def get_client() -> OkxClient:
    return load_client_from_env()


def parse_position(raw: dict[str, Any]) -> Position:
    return Position(
        inst_id=raw.get("instId", ""),
        pos_side=raw.get("posSide", ""),
        position=float(raw.get("pos", 0)),
        avg_px=float(raw.get("avgPx", 0)),
        mark_px=float(raw.get("markPx", 0)),
        upl=float(raw.get("upl", 0)),
        upl_ratio=float(raw.get("uplRatio", 0)),
        mgn_mode=raw.get("mgnMode"),
        lever=float(raw.get("lever")) if raw.get("lever") is not None else None,
        ts=datetime.fromtimestamp(int(raw.get("uTime", "0")) / 1000, tz=timezone.utc)
        if raw.get("uTime")
        else datetime.now(timezone.utc),
    )


async def poll_positions(client: OkxClient, store: List[Position]) -> None:
    while True:
        try:
            data = await client.fetch_positions(inst_type=INST_TYPE)
            store.clear()
            store.extend(parse_position(item) for item in data)
            write_positions_to_excel(store, EXCEL_PATH)
        except Exception as exc:  # noqa: BLE001
            append_trade_log(
                TradeLogEntry(message=f"Position polling failed: {exc}"),
                LOG_PATH,
            )
        await asyncio.sleep(POLL_INTERVAL)


@app.on_event("startup")
async def startup_event() -> None:
    setup_logging(LOG_PATH)
    client = load_client_from_env()
    app.state.client = client
    app.state.positions: List[Position] = []
    app.state.updated_at: Optional[datetime] = None
    app.state.poller = asyncio.create_task(_background_poll())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    poller: asyncio.Task = getattr(app.state, "poller", None)
    if poller:
        poller.cancel()
    client: OkxClient = getattr(app.state, "client", None)
    if client:
        await client.close()


async def _background_poll() -> None:
    client: OkxClient = app.state.client
    store: List[Position] = app.state.positions
    while True:
        try:
            data = await client.fetch_positions(inst_type=INST_TYPE)
            store.clear()
            store.extend(parse_position(item) for item in data)
            app.state.updated_at = datetime.now(timezone.utc)
            write_positions_to_excel(store, EXCEL_PATH)
        except Exception as exc:  # noqa: BLE001
            append_trade_log(TradeLogEntry(message=f"Position polling failed: {exc}"), LOG_PATH)
        await asyncio.sleep(POLL_INTERVAL)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    index_path = Path("frontend/index.html")
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="frontend not built")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/positions", response_model=PositionSnapshot)
async def get_positions() -> PositionSnapshot:
    return PositionSnapshot(updated_at=app.state.updated_at or datetime.now(timezone.utc), positions=app.state.positions)


@app.post("/logs", status_code=201)
async def create_log(entry: TradeLogEntry) -> dict[str, str]:
    append_trade_log(entry, LOG_PATH)
    return {"status": "logged"}


@app.get("/export")
async def export_excel() -> FileResponse:
    if not EXCEL_PATH.exists():
        raise HTTPException(status_code=404, detail="Excel not generated yet")
    return FileResponse(EXCEL_PATH, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="positions.xlsx")


@app.get("/refresh", response_model=PositionSnapshot)
async def manual_refresh(client: OkxClient = Depends(get_client)) -> PositionSnapshot:
    data = await client.fetch_positions(inst_type=INST_TYPE)
    positions = [parse_position(item) for item in data]
    app.state.positions = positions
    app.state.updated_at = datetime.now(timezone.utc)
    write_positions_to_excel(positions, EXCEL_PATH)
    return PositionSnapshot(updated_at=app.state.updated_at, positions=positions)
