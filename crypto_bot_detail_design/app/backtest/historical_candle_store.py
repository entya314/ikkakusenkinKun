from __future__ import annotations

import csv
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.database.db import execute, fetch_all, fetch_one, get_connection
from app.market.candle_service import Candle
from config import settings


class HistoricalCandleStore:
    def ensure_table(self) -> None:
        execute(
            """
            IF OBJECT_ID('dbo.historical_candles', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.historical_candles (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    exchange NVARCHAR(50) NOT NULL,
                    symbol NVARCHAR(20) NOT NULL,
                    timeframe NVARCHAR(10) NOT NULL,
                    open_price DECIMAL(18, 8) NOT NULL,
                    high_price DECIMAL(18, 8) NOT NULL,
                    low_price DECIMAL(18, 8) NOT NULL,
                    close_price DECIMAL(18, 8) NOT NULL,
                    volume DECIMAL(18, 8) NULL,
                    started_at DATETIME2 NOT NULL,
                    ended_at DATETIME2 NOT NULL,
                    imported_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
                    CONSTRAINT UQ_historical_candles_symbol_timeframe_started_at
                        UNIQUE(exchange, symbol, timeframe, started_at)
                );
            END
            """
        )
        execute(
            """
            IF NOT EXISTS (
                SELECT 1
                FROM sys.indexes
                WHERE name = 'IX_historical_candles_symbol_timeframe_started_at'
                  AND object_id = OBJECT_ID('dbo.historical_candles')
            )
            BEGIN
                CREATE INDEX IX_historical_candles_symbol_timeframe_started_at
                ON dbo.historical_candles(symbol, timeframe, started_at);
            END
            """
        )

    def import_csv(self, path: str | Path, symbol: str, timeframe: str) -> int:
        candles = load_candles_from_csv(path, symbol, timeframe)
        return self.save_candles(candles)

    def save_candles(self, candles: list[Candle]) -> int:
        self.ensure_table()
        if not candles:
            return 0

        first = candles[0]
        rows = fetch_all(
            """
            SELECT started_at
            FROM dbo.historical_candles
            WHERE exchange = ? AND symbol = ? AND timeframe = ?
            """,
            [settings.exchange_name, first.symbol, first.timeframe],
        )
        existing_starts = {row[0] for row in rows}
        new_candles = [candle for candle in candles if _without_tz(candle.started_at) not in existing_starts]
        if not new_candles:
            return 0

        params = [
            (
                settings.exchange_name,
                candle.symbol,
                candle.timeframe,
                candle.open_price,
                candle.high_price,
                candle.low_price,
                candle.close_price,
                candle.volume,
                _without_tz(candle.started_at),
                _without_tz(candle.ended_at),
            )
            for candle in new_candles
        ]
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(
                """
                INSERT INTO dbo.historical_candles
                (exchange, symbol, timeframe, open_price, high_price, low_price, close_price, volume, started_at, ended_at, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSDATETIME())
                """,
                params,
            )
        return len(new_candles)

    def load_candles(self, symbol: str, timeframe: str = "5m", limit: int | None = None) -> list[Candle]:
        self.ensure_table()
        if limit is None or limit <= 0:
            rows = fetch_all(
                """
                SELECT symbol, timeframe, open_price, high_price, low_price, close_price, volume, started_at, ended_at
                FROM dbo.historical_candles
                WHERE exchange = ? AND symbol = ? AND timeframe = ?
                ORDER BY started_at ASC
                """,
                [settings.exchange_name, symbol, timeframe],
            )
        else:
            rows = fetch_all(
                """
                SELECT symbol, timeframe, open_price, high_price, low_price, close_price, volume, started_at, ended_at
                FROM (
                    SELECT TOP (?) symbol, timeframe, open_price, high_price, low_price, close_price, volume, started_at, ended_at
                    FROM dbo.historical_candles
                    WHERE exchange = ? AND symbol = ? AND timeframe = ?
                    ORDER BY started_at DESC
                ) AS recent
                ORDER BY started_at ASC
                """,
                [limit, settings.exchange_name, symbol, timeframe],
            )
        return [_row_to_candle(row) for row in rows]

    def count(self, symbol: str, timeframe: str = "5m") -> int:
        self.ensure_table()
        row = fetch_one(
            """
            SELECT COUNT(*)
            FROM dbo.historical_candles
            WHERE exchange = ? AND symbol = ? AND timeframe = ?
            """,
            [settings.exchange_name, symbol, timeframe],
        )
        return int(row[0]) if row else 0

    def date_range(self, symbol: str, timeframe: str = "5m") -> tuple[datetime | None, datetime | None]:
        self.ensure_table()
        row = fetch_one(
            """
            SELECT MIN(started_at), MAX(started_at)
            FROM dbo.historical_candles
            WHERE exchange = ? AND symbol = ? AND timeframe = ?
            """,
            [settings.exchange_name, symbol, timeframe],
        )
        if row is None:
            return None, None
        return row[0], row[1]


def load_candles_from_csv(path: str | Path, symbol: str, timeframe: str) -> list[Candle]:
    minutes = _timeframe_to_minutes(timeframe)
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        candles = []
        for row in reader:
            normalized = {_normalize_key(key): value for key, value in row.items()}
            started_at = _parse_datetime(_first(normalized, "started_at", "datetime", "date", "timestamp", "time"))
            ended_at = _parse_datetime(normalized["ended_at"]) if normalized.get("ended_at") else started_at + timedelta(minutes=minutes)
            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    open_price=Decimal(str(_first(normalized, "open", "open_price"))),
                    high_price=Decimal(str(_first(normalized, "high", "high_price"))),
                    low_price=Decimal(str(_first(normalized, "low", "low_price"))),
                    close_price=Decimal(str(_first(normalized, "close", "close_price"))),
                    volume=Decimal(str(normalized["volume"])) if normalized.get("volume") not in {None, ""} else None,
                    started_at=started_at,
                    ended_at=ended_at,
                )
            )
    return sorted(candles, key=lambda item: item.started_at)


def _row_to_candle(row) -> Candle:
    return Candle(
        symbol=row[0],
        timeframe=row[1],
        open_price=Decimal(str(row[2])),
        high_price=Decimal(str(row[3])),
        low_price=Decimal(str(row[4])),
        close_price=Decimal(str(row[5])),
        volume=Decimal(str(row[6])) if row[6] is not None else None,
        started_at=row[7],
        ended_at=row[8],
    )


def _normalize_key(key: str | None) -> str:
    return (key or "").strip().lower().replace(" ", "_")


def _first(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        if row.get(key) not in {None, ""}:
            return row[key]
    raise ValueError(f"CSVに必要な列がありません: {', '.join(keys)}")


def _parse_datetime(value: str) -> datetime:
    normalized = str(value).strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(normalized).replace(tzinfo=None)


def _without_tz(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.replace(tzinfo=None)


def _timeframe_to_minutes(timeframe: str) -> int:
    value = timeframe.strip().lower()
    if value.endswith("m"):
        return int(value[:-1])
    if value.endswith("h"):
        return int(value[:-1]) * 60
    raise ValueError(f"未対応の時間足です: {timeframe}")
