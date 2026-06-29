from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.database.db import execute, fetch_one
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

    def open_position(
        self,
        entry_order_id: int | None,
        entry_price: Decimal,
        amount: Decimal,
        take_profit_price: Decimal | None,
        stop_loss_price: Decimal | None,
    ) -> None:
        execute(
            """
            INSERT INTO dbo.positions
            (symbol, status, entry_order_id, entry_price, amount, take_profit_price, stop_loss_price, opened_at)
            VALUES (?, N'OPEN', ?, ?, ?, ?, ?, ?)
            """,
            [
                settings.symbol,
                entry_order_id,
                entry_price,
                amount,
                take_profit_price,
                stop_loss_price,
                datetime.now(),
            ],
        )

    def close_position(
        self,
        position_id: int,
        exit_order_id: int | None,
        exit_price: Decimal | None = None,
        exit_reason: str | None = None,
    ) -> None:
        position = fetch_one(
            """
            SELECT symbol, entry_price, amount, opened_at
            FROM dbo.positions
            WHERE id = ?
            """,
            [position_id],
        )
        execute(
            """
            UPDATE dbo.positions
            SET status = N'CLOSED', exit_order_id = ?, closed_at = ?
            WHERE id = ? AND status = N'OPEN'
            """,
            [exit_order_id, datetime.now(), position_id],
        )
        if position is None or exit_price is None:
            return

        symbol, entry_price, amount, opened_at = position
        entry_price = Decimal(str(entry_price))
        amount = Decimal(str(amount))
        gross_profit_jpy = (exit_price - entry_price) * amount
        profit_rate = (exit_price - entry_price) / entry_price if entry_price else Decimal("0")
        execute(
            """
            INSERT INTO dbo.trades
            (position_id, symbol, entry_price, exit_price, amount, gross_profit_jpy, fee_jpy, net_profit_jpy, profit_rate, exit_reason, opened_at, closed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                position_id,
                symbol,
                entry_price,
                exit_price,
                amount,
                gross_profit_jpy,
                None,
                gross_profit_jpy,
                profit_rate,
                exit_reason or "EXIT",
                opened_at,
                datetime.now(),
            ],
        )
