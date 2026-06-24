from __future__ import annotations

import json
from datetime import datetime

from app.database.db import execute
from app.exchange.exchange_client import CoincheckClient
from config import settings


class OrderService:
    def __init__(self, client: CoincheckClient) -> None:
        self.client = client

    def record_order(
        self,
        side: str,
        order_type: str,
        amount: float,
        price: float | None,
        status: str,
        purpose: str,
        raw_response: dict | None = None,
    ) -> None:
        execute(
            """
            INSERT INTO dbo.orders
            (exchange, exchange_order_id, symbol, side, order_type, price, amount, status, purpose, raw_response, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                settings.exchange_name,
                str(raw_response.get("id")) if raw_response and raw_response.get("id") else None,
                settings.symbol,
                side,
                order_type,
                price,
                amount,
                status,
                purpose,
                json.dumps(raw_response, ensure_ascii=False) if raw_response else None,
                datetime.now(),
            ],
        )

    def market_buy(self, amount_jpy: int) -> None:
        if not settings.trading_enabled:
            self.record_order("BUY", "MARKET", amount_jpy, None, "CREATED", "ENTRY", None)
            return

        response = self.client.create_market_buy_order(settings.symbol.lower(), amount_jpy)
        self.record_order("BUY", "MARKET", amount_jpy, None, "SENT", "ENTRY", response)

    def limit_sell(self, amount: float, price: float) -> None:
        if not settings.trading_enabled:
            self.record_order("SELL", "LIMIT", amount, price, "CREATED", "TAKE_PROFIT", None)
            return

        response = self.client.create_limit_sell_order(settings.symbol.lower(), amount, price)
        self.record_order("SELL", "LIMIT", amount, price, "SENT", "TAKE_PROFIT", response)

    def market_sell(self, amount: float, purpose: str = "STOP_LOSS") -> None:
        if not settings.trading_enabled:
            self.record_order("SELL", "MARKET", amount, None, "CREATED", purpose, None)
            return

        response = self.client.create_market_sell_order(settings.symbol.lower(), amount)
        self.record_order("SELL", "MARKET", amount, None, "SENT", purpose, response)
