from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import requests

from app.common.exceptions import ExchangeApiError
from config import settings


class CoincheckClient:
    """Coincheck APIクライアント雛形。

    注意:
    - private APIの注文系は本番前に必ず公式仕様で確認すること。
    - ここでは実装箇所が分かるように骨組みを置く。
    """

    def __init__(self) -> None:
        self.base_url = settings.coincheck_base_url.rstrip("/")
        self.access_key = settings.coincheck_access_key
        self.secret_key = settings.coincheck_secret_key.encode("utf-8")

    def _headers(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, str]:
        nonce = str(int(time.time() * 1000))
        body_text = json.dumps(body or {}, separators=(",", ":")) if body else ""
        message = nonce + self.base_url + path + body_text
        signature = hmac.new(self.secret_key, message.encode("utf-8"), hashlib.sha256).hexdigest()
        return {
            "ACCESS-KEY": self.access_key,
            "ACCESS-NONCE": nonce,
            "ACCESS-SIGNATURE": signature,
            "Content-Type": "application/json",
        }

    def get_ticker(self, pair: str = "btc_jpy") -> dict[str, Any]:
        url = f"{self.base_url}/api/ticker"
        response = requests.get(url, params={"pair": pair}, timeout=10)
        if not response.ok:
            raise ExchangeApiError(f"ticker取得失敗: {response.status_code} {response.text}")
        return response.json()

    def get_balance(self) -> dict[str, Any]:
        path = "/api/accounts/balance"
        url = f"{self.base_url}{path}"
        response = requests.get(url, headers=self._headers("GET", path), timeout=10)
        if not response.ok:
            raise ExchangeApiError(f"残高取得失敗: {response.status_code} {response.text}")
        return response.json()

    def create_market_buy_order(self, pair: str, market_buy_amount_jpy: int) -> dict[str, Any]:
        """成行買い注文。

        本番前にAPI仕様、最小注文金額、パラメータ名を確認すること。
        """
        raise NotImplementedError("Coincheckの成行買い注文API実装を追加してください")

    def create_limit_sell_order(self, pair: str, amount: float, price: float) -> dict[str, Any]:
        """利確用の指値売り注文。"""
        raise NotImplementedError("Coincheckの指値売り注文API実装を追加してください")

    def create_market_sell_order(self, pair: str, amount: float) -> dict[str, Any]:
        """損切り・緊急決済用の成行売り注文。"""
        raise NotImplementedError("Coincheckの成行売り注文API実装を追加してください")
