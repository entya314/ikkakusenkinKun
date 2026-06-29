from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.database.db import execute, fetch_all, fetch_one
from config import settings


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal | None
    started_at: datetime
    ended_at: datetime


class CandleService:
    """Build and load live candles from collected ticker prices."""

    def build_from_market_prices(self, symbol: str, timeframe: str) -> Candle | None:
        minutes = _timeframe_to_minutes(timeframe)
        bucket_start = _floor_time(datetime.now(), minutes)
        bucket_end = bucket_start + timedelta(minutes=minutes)

        rows = fetch_all(
            """
            SELECT price, collected_at
            FROM dbo.market_prices
            WHERE exchange = ? AND symbol = ? AND collected_at >= ? AND collected_at < ?
            ORDER BY collected_at ASC
            """,
            [settings.exchange_name, symbol, bucket_start, bucket_end],
        )
        if not rows:
            return None

        prices = [Decimal(str(row[0])) for row in rows]
        candle = Candle(
            symbol=symbol,
            timeframe=timeframe,
            open_price=prices[0],
            high_price=max(prices),
            low_price=min(prices),
            close_price=prices[-1],
            volume=None,
            started_at=bucket_start,
            ended_at=bucket_end,
        )
        self._upsert_candle(candle)
        return candle

    def get_recent_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        rows = fetch_all(
            """
            SELECT symbol, timeframe, open_price, high_price, low_price, close_price, volume, started_at, ended_at
            FROM (
                SELECT TOP (?) symbol, timeframe, open_price, high_price, low_price, close_price, volume, started_at, ended_at
                FROM dbo.candles
                WHERE exchange = ? AND symbol = ? AND timeframe = ?
                ORDER BY started_at DESC
            ) AS recent
            ORDER BY started_at ASC
            """,
            [limit, settings.exchange_name, symbol, timeframe],
        )
        return [_row_to_candle(row) for row in rows]

    def _upsert_candle(self, candle: Candle) -> None:
        existing = fetch_one(
            """
            SELECT TOP 1 id
            FROM dbo.candles
            WHERE exchange = ? AND symbol = ? AND timeframe = ? AND started_at = ?
            """,
            [settings.exchange_name, candle.symbol, candle.timeframe, candle.started_at],
        )
        if existing:
            execute(
                """
                UPDATE dbo.candles
                SET open_price = ?, high_price = ?, low_price = ?, close_price = ?, volume = ?, ended_at = ?
                WHERE id = ?
                """,
                [
                    candle.open_price,
                    candle.high_price,
                    candle.low_price,
                    candle.close_price,
                    candle.volume,
                    candle.ended_at,
                    existing[0],
                ],
            )
            return

        execute(
            """
            INSERT INTO dbo.candles
            (exchange, symbol, timeframe, open_price, high_price, low_price, close_price, volume, started_at, ended_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                settings.exchange_name,
                candle.symbol,
                candle.timeframe,
                candle.open_price,
                candle.high_price,
                candle.low_price,
                candle.close_price,
                candle.volume,
                candle.started_at,
                candle.ended_at,
            ],
        )


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


def _timeframe_to_minutes(timeframe: str) -> int:
    value = timeframe.strip().lower()
    if value.endswith("m"):
        return int(value[:-1])
    if value.endswith("h"):
        return int(value[:-1]) * 60
    raise ValueError(f"Unsupported timeframe: {timeframe}")


def _floor_time(value: datetime, minutes: int) -> datetime:
    minute = value.minute - (value.minute % minutes)
    return value.replace(minute=minute, second=0, microsecond=0)
