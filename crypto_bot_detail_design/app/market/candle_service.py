from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


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
    """ローソク足生成・取得サービス雛形。"""

    def build_from_market_prices(self, symbol: str, timeframe: str) -> Candle | None:
        """market_pricesからローソク足を生成する。

        TODO:
        - timeframeごとの集計範囲を決める
        - SQLでOHLCVを集計する
        - candlesへUPSERTする
        """
        return None

    def get_recent_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        """直近ローソク足を取得する。"""
        return []
