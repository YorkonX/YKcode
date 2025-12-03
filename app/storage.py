from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .models import Position, TradeLogEntry

logger = logging.getLogger(__name__)


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


def append_trade_log(entry: TradeLogEntry, log_path: Path) -> None:
    logger.info("%s | context=%s", entry.message, entry.context)
    log_path.touch(exist_ok=True)


def write_positions_to_excel(positions: Iterable[Position], xlsx_path: Path) -> None:
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    rows: List[dict] = []
    for pos in positions:
        rows.append(
            {
                "instId": pos.inst_id,
                "posSide": pos.pos_side,
                "position": pos.position,
                "avgPx": pos.avg_px,
                "markPx": pos.mark_px,
                "upl": pos.upl,
                "uplRatio": pos.upl_ratio,
                "mgnMode": pos.mgn_mode,
                "lever": pos.lever,
                "timestamp": pos.ts,
            }
        )
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
