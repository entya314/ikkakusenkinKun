from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.database.db import execute
from app.exchange.exchange_client import CoincheckClient
from config import settings


class MarketDataService:
    def __init__(self, client: CoincheckClient) -> None:
        self.client = client

    def collect_current_price(self) -> Decimal:
        ticker = self.client.get_ticker(pair=settings.symbol.lower())
        price = Decimal(str(ticker.get("last")))

        execute(
            """
            INSERT INTO dbo.market_prices
            (exchange, symbol, price, bid, ask, volume, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                settings.exchange_name,
                settings.symbol,
                price,
                Decimal(str(ticker.get("bid"))) if ticker.get("bid") is not None else None,
                Decimal(str(ticker.get("ask"))) if ticker.get("ask") is not None else None,
                Decimal(str(ticker.get("volume"))) if ticker.get("volume") is not None else None,
                datetime.now(),
            ],
        )
        return price
