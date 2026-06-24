from __future__ import annotations

from app.database.db import fetch_one
from config import settings


class PositionService:
    def has_open_position(self) -> bool:
        row = fetch_one(
            """
            SELECT TOP 1 id
            FROM dbo.positions
            WHERE symbol = ? AND status = N'OPEN'
            ORDER BY opened_at DESC
            """,
            [settings.symbol],
        )
        return row is not None

    def get_open_position(self):
        return fetch_one(
            """
            SELECT TOP 1 id, symbol, entry_price, amount, take_profit_price, stop_loss_price, opened_at
            FROM dbo.positions
            WHERE symbol = ? AND status = N'OPEN'
            ORDER BY opened_at DESC
            """,
            [settings.symbol],
        )
