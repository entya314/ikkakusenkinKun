from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from app.common.exceptions import ExchangeApiError
from config import settings


class CoincheckClient:
    """Coincheck APIクライアント。"""

    def __init__(self) -> None:
        self.base_url = settings.coincheck_base_url.rstrip("/")
        self.access_key = settings.coincheck_access_key
        self.secret_key = settings.coincheck_secret_key.encode("utf-8")

    def _encode_body(self, body: dict[str, Any] | None = None) -> str:
        return urlencode(body or {}) if body else ""

    def _headers(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, str]:
        nonce = str(int(time.time() * 1000))
        body_text = self._encode_body(body)
        message = nonce + self.base_url + path + body_text
        signature = hmac.new(self.secret_key, message.encode("utf-8"), hashlib.sha256).hexdigest()
        return {
            "ACCESS-KEY": self.access_key,
            "ACCESS-NONCE": nonce,
            "ACCESS-SIGNATURE": signature,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _ensure_private_api_credentials(self) -> None:
        if not self.access_key or not self.secret_key:
            raise ExchangeApiError("Coincheck APIキーが未設定です")

    def _post_private(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        self._ensure_private_api_credentials()

        url = f"{self.base_url}{path}"
        response = requests.post(url, data=self._encode_body(body), headers=self._headers("POST", path, body), timeout=10)
        if not response.ok:
            raise ExchangeApiError(f"Coincheck API POST失敗: {response.status_code} {response.text}")

        data = response.json()
        if data.get("success") is False:
            raise ExchangeApiError(f"Coincheck API処理失敗: {data}")
        return data

    def get_ticker(self, pair: str = "btc_jpy") -> dict[str, Any]:
        url = f"{self.base_url}/api/ticker"
        response = requests.get(url, params={"pair": pair}, timeout=10)
        if not response.ok:
            raise ExchangeApiError(f"ticker取得失敗: {response.status_code} {response.text}")
        return response.json()

    def get_balance(self) -> dict[str, Any]:
        self._ensure_private_api_credentials()

        path = "/api/accounts/balance"
        url = f"{self.base_url}{path}"
        response = requests.get(url, headers=self._headers("GET", path), timeout=10)
        if not response.ok:
            raise ExchangeApiError(f"残高取得失敗: {response.status_code} {response.text}")
        return response.json()

    def create_market_buy_order(self, pair: str, market_buy_amount_jpy: int) -> dict[str, Any]:
        """成行買い注文。

        Coincheckの成行買いはBTC数量ではなく、利用するJPY金額を送る。
        """
        body = {
            "pair": pair,
            "order_type": "market_buy",
            "market_buy_amount": market_buy_amount_jpy,
        }
        return self._post_private("/api/exchange/orders", body)

    def create_limit_sell_order(self, pair: str, amount: float, price: float) -> dict[str, Any]:
        """利確用の指値売り注文。"""
        body = {
            "pair": pair,
            "order_type": "sell",
            "amount": amount,
            "rate": price,
        }
        return self._post_private("/api/exchange/orders", body)

    def create_market_sell_order(self, pair: str, amount: float) -> dict[str, Any]:
        """損切り・緊急決済用の成行売り注文。"""
        body = {
            "pair": pair,
            "order_type": "market_sell",
            "amount": amount,
        }
        return self._post_private("/api/exchange/orders", body)
