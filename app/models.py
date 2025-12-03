from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Position(BaseModel):
    inst_id: str = Field(..., description="Instrument identifier, e.g. BTC-USDT-SWAP")
    pos_side: str = Field(..., description="Position side, e.g. long/short")
    position: float = Field(..., description="Position size")
    avg_px: float = Field(..., description="Average entry price")
    mark_px: float = Field(..., description="Current mark price")
    upl: float = Field(..., description="Unrealized P&L")
    upl_ratio: float = Field(..., description="Unrealized P&L ratio")
    mgn_mode: Optional[str] = Field(None, description="Margin mode")
    lever: Optional[float] = Field(None, description="Leverage")
    ts: datetime = Field(default_factory=datetime.utcnow, description="Fetched time")


class PositionSnapshot(BaseModel):
    updated_at: datetime
    positions: List[Position]


class TradeLogEntry(BaseModel):
    message: str
    context: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
