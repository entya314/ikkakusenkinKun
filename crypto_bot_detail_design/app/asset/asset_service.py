from __future__ import annotations

from decimal import Decimal

from app.exchange.exchange_client import CoincheckClient


class AssetService:
    def __init__(self, client: CoincheckClient) -> None:
        self.client = client

    def get_balance(self) -> dict:
        return self.client.get_balance()

    def calculate_estimated_total_jpy(
        self,
        jpy_balance: Decimal,
        crypto_amount: Decimal,
        current_price: Decimal,
    ) -> Decimal:
        return jpy_balance + crypto_amount * current_price
