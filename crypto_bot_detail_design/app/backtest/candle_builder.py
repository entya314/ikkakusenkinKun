from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from app.backtest.models import HistoricalTrade
from app.market.candle_service import Candle


def _timeframe_to_minutes(timeframe: str) -> int:
    value = timeframe.strip().lower()
    if value.endswith("m"):
        return int(value[:-1])
    if value.endswith("h"):
        return int(value[:-1]) * 60
    raise ValueError(f"未対応の時間足です: {timeframe}")


def _floor_time(value: datetime, minutes: int) -> datetime:
    minute = value.minute - (value.minute % minutes)
    return value.replace(minute=minute, second=0, microsecond=0)


def build_candles_from_trades(
    trades: list[HistoricalTrade],
    symbol: str,
    timeframe: str,
) -> list[Candle]:
    minutes = _timeframe_to_minutes(timeframe)
    buckets: dict[datetime, list[HistoricalTrade]] = defaultdict(list)

    for trade in sorted(trades, key=lambda item: item.created_at):
        buckets[_floor_time(trade.created_at, minutes)].append(trade)

    candles: list[Candle] = []
    for started_at in sorted(buckets):
        items = buckets[started_at]
        prices = [item.price for item in items]
        volume = sum((item.amount for item in items), Decimal("0"))
        candles.append(
            Candle(
                symbol=symbol,
                timeframe=timeframe,
                open_price=prices[0],
                high_price=max(prices),
                low_price=min(prices),
                close_price=prices[-1],
                volume=volume,
                started_at=started_at,
                ended_at=started_at + timedelta(minutes=minutes),
            )
        )
    return candles
