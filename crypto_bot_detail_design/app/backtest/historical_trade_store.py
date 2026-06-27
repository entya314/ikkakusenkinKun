from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.backtest.models import HistoricalTrade
from app.database.db import execute, fetch_all, fetch_one, get_connection
from config import settings


class HistoricalTradeStore:
    def ensure_table(self) -> None:
        execute(
            """
            IF OBJECT_ID('dbo.historical_trades', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.historical_trades (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    exchange NVARCHAR(50) NOT NULL,
                    symbol NVARCHAR(20) NOT NULL,
                    exchange_trade_id BIGINT NOT NULL,
                    price DECIMAL(18, 8) NOT NULL,
                    amount DECIMAL(18, 8) NOT NULL,
                    side NVARCHAR(20) NULL,
                    traded_at DATETIME2 NOT NULL,
                    fetched_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
                    CONSTRAINT UQ_historical_trades_exchange_symbol_trade_id
                        UNIQUE(exchange, symbol, exchange_trade_id)
                );
            END
            """
        )
        execute(
            """
            IF NOT EXISTS (
                SELECT 1
                FROM sys.indexes
                WHERE name = 'IX_historical_trades_symbol_traded_at'
                  AND object_id = OBJECT_ID('dbo.historical_trades')
            )
            BEGIN
                CREATE INDEX IX_historical_trades_symbol_traded_at
                ON dbo.historical_trades(symbol, traded_at);
            END
            """
        )

    def save_trades(self, symbol: str, trades: list[HistoricalTrade]) -> int:
        self.ensure_table()
        if not trades:
            return 0

        rows = fetch_all(
            """
            SELECT exchange_trade_id
            FROM dbo.historical_trades
            WHERE exchange = ? AND symbol = ?
            """,
            [settings.exchange_name, symbol],
        )
        existing_ids = {int(row[0]) for row in rows}
        new_trades = [trade for trade in trades if trade.id not in existing_ids]
        if not new_trades:
            return 0

        params = [
            (
                settings.exchange_name,
                symbol,
                trade.id,
                trade.price,
                trade.amount,
                trade.side,
                _without_tz(trade.created_at),
            )
            for trade in new_trades
        ]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(
                """
                INSERT INTO dbo.historical_trades
                (exchange, symbol, exchange_trade_id, price, amount, side, traded_at, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, SYSDATETIME())
                """,
                params,
            )
        return len(new_trades)

    def load_trades(self, symbol: str, limit: int | None = None) -> list[HistoricalTrade]:
        self.ensure_table()
        if limit is None or limit <= 0:
            rows = fetch_all(
                """
                SELECT exchange_trade_id, price, amount, traded_at, side
                FROM dbo.historical_trades
                WHERE exchange = ? AND symbol = ?
                ORDER BY traded_at ASC
                """,
                [settings.exchange_name, symbol],
            )
        else:
            rows = fetch_all(
                """
                SELECT exchange_trade_id, price, amount, traded_at, side
                FROM (
                    SELECT TOP (?) exchange_trade_id, price, amount, traded_at, side
                    FROM dbo.historical_trades
                    WHERE exchange = ? AND symbol = ?
                    ORDER BY traded_at DESC
                ) AS recent
                ORDER BY traded_at ASC
                """,
                [limit, settings.exchange_name, symbol],
            )
        return [
            HistoricalTrade(
                id=int(row[0]),
                price=Decimal(str(row[1])),
                amount=Decimal(str(row[2])),
                created_at=row[3],
                side=row[4],
            )
            for row in rows
        ]

    def count(self, symbol: str) -> int:
        self.ensure_table()
        row = fetch_one(
            """
            SELECT COUNT(*)
            FROM dbo.historical_trades
            WHERE exchange = ? AND symbol = ?
            """,
            [settings.exchange_name, symbol],
        )
        return int(row[0]) if row else 0

    def date_range(self, symbol: str) -> tuple[datetime | None, datetime | None]:
        self.ensure_table()
        row = fetch_one(
            """
            SELECT MIN(traded_at), MAX(traded_at)
            FROM dbo.historical_trades
            WHERE exchange = ? AND symbol = ?
            """,
            [settings.exchange_name, symbol],
        )
        if row is None:
            return None, None
        return row[0], row[1]


def _without_tz(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.replace(tzinfo=None)
