from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.common.exceptions import OrderExecutionError
from app.database.db import fetch_one, get_connection
from app.exchange.exchange_client import CoincheckClient
from config import settings


@dataclass(frozen=True)
class OrderResult:
    order_id: int
    status: str
    raw_response: dict | None


class OrderService:
    def __init__(self, client: CoincheckClient) -> None:
        self.client = client

    def record_order(
        self,
        side: str,
        order_type: str,
        amount: float | Decimal | int,
        price: float | Decimal | None,
        status: str,
        purpose: str,
        raw_response: dict | None = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dbo.orders
                (exchange, exchange_order_id, symbol, side, order_type, price, amount, status, purpose, raw_response, created_at)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
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
                ),
            )
            row = cursor.fetchone()
        return int(row[0])

    def market_buy(self, amount_jpy: int) -> OrderResult:
        self._validate_market_buy_amount(amount_jpy)
        if not settings.trading_enabled:
            order_id = self.record_order("BUY", "MARKET", amount_jpy, None, "CREATED", "ENTRY", None)
            return OrderResult(order_id, "CREATED", None)

        self._ensure_live_trading_allowed()
        self._ensure_no_recent_order("BUY", "ENTRY")
        self._ensure_jpy_balance(amount_jpy)

        response = self.client.create_market_buy_order(settings.symbol.lower(), amount_jpy)
        order_id = self.record_order("BUY", "MARKET", amount_jpy, None, "SENT", "ENTRY", response)
        return OrderResult(order_id, "SENT", response)

    def limit_sell(self, amount: float | Decimal, price: float | Decimal) -> OrderResult:
        if not settings.trading_enabled:
            order_id = self.record_order("SELL", "LIMIT", amount, price, "CREATED", "TAKE_PROFIT", None)
            return OrderResult(order_id, "CREATED", None)

        self._ensure_live_trading_allowed()
        self._ensure_no_recent_order("SELL", "TAKE_PROFIT")

        response = self.client.create_limit_sell_order(settings.symbol.lower(), float(amount), float(price))
        order_id = self.record_order("SELL", "LIMIT", amount, price, "SENT", "TAKE_PROFIT", response)
        return OrderResult(order_id, "SENT", response)

    def market_sell(self, amount: float | Decimal, purpose: str = "STOP_LOSS") -> OrderResult:
        sell_amount = Decimal(str(amount))
        if sell_amount <= 0:
            raise OrderExecutionError("Sell amount must be greater than zero.")

        if not settings.trading_enabled:
            order_id = self.record_order("SELL", "MARKET", sell_amount, None, "CREATED", purpose, None)
            return OrderResult(order_id, "CREATED", None)

        self._ensure_live_trading_allowed()
        self._ensure_no_recent_order("SELL", purpose)
        available_amount = self._available_base_amount()
        if available_amount <= 0:
            raise OrderExecutionError(f"{settings.base_symbol} balance is not available for sell.")
        if available_amount < sell_amount:
            sell_amount = available_amount

        response = self.client.create_market_sell_order(settings.symbol.lower(), float(sell_amount))
        order_id = self.record_order("SELL", "MARKET", sell_amount, None, "SENT", purpose, response)
        return OrderResult(order_id, "SENT", response)

    def _validate_market_buy_amount(self, amount_jpy: int) -> None:
        if amount_jpy < settings.min_order_amount_jpy:
            raise OrderExecutionError(
                f"Order amount {amount_jpy} JPY is below MIN_ORDER_AMOUNT_JPY={settings.min_order_amount_jpy}."
            )

    def _ensure_live_trading_allowed(self) -> None:
        row = fetch_one(
            """
            SELECT TOP 1 emergency_stop, is_trading_enabled, reason
            FROM dbo.bot_status
            ORDER BY id DESC
            """
        )
        if row is None:
            raise OrderExecutionError("bot_status is missing.")
        emergency_stop, is_trading_enabled, reason = row
        if emergency_stop:
            raise OrderExecutionError(f"Emergency stop is enabled: {reason}")
        if not is_trading_enabled:
            raise OrderExecutionError("DB bot_status.is_trading_enabled is off.")

    def _ensure_no_recent_order(self, side: str, purpose: str) -> None:
        row = fetch_one(
            """
            SELECT TOP 1 id, status, created_at
            FROM dbo.orders
            WHERE symbol = ? AND side = ? AND purpose = ?
              AND created_at >= DATEADD(second, ?, SYSDATETIME())
            ORDER BY created_at DESC
            """,
            [settings.symbol, side, purpose, -settings.order_cooldown_seconds],
        )
        if row is not None:
            raise OrderExecutionError(
                f"Recent {side} {purpose} order exists within {settings.order_cooldown_seconds} seconds."
            )

    def _ensure_jpy_balance(self, amount_jpy: int) -> None:
        balance = self.client.get_balance()
        available_jpy = Decimal(str(balance.get("jpy", "0")))
        if available_jpy < Decimal(amount_jpy):
            raise OrderExecutionError(f"JPY balance is insufficient: {available_jpy} < {amount_jpy}.")

    def _available_base_amount(self) -> Decimal:
        balance = self.client.get_balance()
        value = balance.get(settings.base_symbol.lower(), "0")
        return Decimal(str(value))
