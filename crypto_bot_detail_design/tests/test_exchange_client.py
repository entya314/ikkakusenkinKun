import hashlib
import hmac
from unittest.mock import Mock

import pytest

from app.common.exceptions import ExchangeApiError
from app.exchange.exchange_client import CoincheckClient


def _client() -> CoincheckClient:
    client = CoincheckClient()
    client.base_url = "https://coincheck.com"
    client.access_key = "access-key"
    client.secret_key = b"secret-key"
    return client


def test_headers_sign_with_nonce_url_and_form_body(monkeypatch):
    monkeypatch.setattr("app.exchange.exchange_client.time.time", lambda: 1234.567)
    client = _client()
    body = {"pair": "btc_jpy", "order_type": "market_buy", "market_buy_amount": 10000}

    headers = client._headers("POST", "/api/exchange/orders", body)

    body_text = "pair=btc_jpy&order_type=market_buy&market_buy_amount=10000"
    message = "1234567" + "https://coincheck.com" + "/api/exchange/orders" + body_text
    expected = hmac.new(b"secret-key", message.encode("utf-8"), hashlib.sha256).hexdigest()
    assert headers["ACCESS-KEY"] == "access-key"
    assert headers["ACCESS-NONCE"] == "1234567"
    assert headers["ACCESS-SIGNATURE"] == expected
    assert headers["Content-Type"] == "application/x-www-form-urlencoded"


def test_create_market_buy_order_posts_jpy_amount(monkeypatch):
    client = _client()
    response = Mock(ok=True)
    response.json.return_value = {"success": True, "id": 12345}
    post = Mock(return_value=response)
    monkeypatch.setattr("app.exchange.exchange_client.requests.post", post)

    result = client.create_market_buy_order("btc_jpy", 10000)

    assert result == {"success": True, "id": 12345}
    post.assert_called_once()
    _, kwargs = post.call_args
    assert kwargs["data"] == "pair=btc_jpy&order_type=market_buy&market_buy_amount=10000"


def test_create_limit_sell_order_posts_rate_and_amount(monkeypatch):
    client = _client()
    response = Mock(ok=True)
    response.json.return_value = {"success": True, "id": 12345}
    post = Mock(return_value=response)
    monkeypatch.setattr("app.exchange.exchange_client.requests.post", post)

    result = client.create_limit_sell_order("btc_jpy", 0.01, 10000000)

    assert result["success"] is True
    _, kwargs = post.call_args
    assert kwargs["data"] == "pair=btc_jpy&order_type=sell&amount=0.01&rate=10000000"


def test_create_market_sell_order_posts_amount(monkeypatch):
    client = _client()
    response = Mock(ok=True)
    response.json.return_value = {"success": True, "id": 12345}
    post = Mock(return_value=response)
    monkeypatch.setattr("app.exchange.exchange_client.requests.post", post)

    result = client.create_market_sell_order("btc_jpy", 0.01)

    assert result["success"] is True
    _, kwargs = post.call_args
    assert kwargs["data"] == "pair=btc_jpy&order_type=market_sell&amount=0.01"


def test_private_api_requires_credentials():
    client = CoincheckClient()
    client.access_key = ""
    client.secret_key = b""

    with pytest.raises(ExchangeApiError, match="APIキー"):
        client.create_market_sell_order("btc_jpy", 0.01)
