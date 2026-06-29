from types import SimpleNamespace

import pytest

from app.common.exceptions import OrderExecutionError
from app.order.order_service import OrderService


class FakeClient:
    def __init__(self, balance=None):
        self.balance = balance or {"jpy": "10000", "btc": "0.01"}
        self.market_buy_calls = []
        self.market_sell_calls = []

    def get_balance(self):
        return self.balance

    def create_market_buy_order(self, pair, market_buy_amount_jpy):
        self.market_buy_calls.append((pair, market_buy_amount_jpy))
        return {"success": True, "id": 123}

    def create_market_sell_order(self, pair, amount):
        self.market_sell_calls.append((pair, amount))
        return {"success": True, "id": 456}


def _settings(trading_enabled: bool):
    return SimpleNamespace(
        exchange_name="coincheck",
        symbol="BTC_JPY",
        base_symbol="BTC",
        trading_enabled=trading_enabled,
        min_order_amount_jpy=500,
        order_cooldown_seconds=300,
    )


def test_market_buy_dry_run_records_order_without_calling_api(monkeypatch):
    client = FakeClient()
    service = OrderService(client)

    monkeypatch.setattr("app.order.order_service.settings", _settings(trading_enabled=False))
    monkeypatch.setattr(service, "record_order", lambda *args, **kwargs: 10)

    result = service.market_buy(500)

    assert result.order_id == 10
    assert result.status == "CREATED"
    assert client.market_buy_calls == []


def test_market_buy_live_checks_balance_and_sends_order(monkeypatch):
    client = FakeClient(balance={"jpy": "1000", "btc": "0"})
    service = OrderService(client)

    monkeypatch.setattr("app.order.order_service.settings", _settings(trading_enabled=True))
    monkeypatch.setattr("app.order.order_service.fetch_one", lambda *args, **kwargs: (0, 1, None))
    monkeypatch.setattr(service, "_ensure_no_recent_order", lambda side, purpose: None)
    monkeypatch.setattr(service, "record_order", lambda *args, **kwargs: 11)

    result = service.market_buy(500)

    assert result.order_id == 11
    assert result.status == "SENT"
    assert client.market_buy_calls == [("btc_jpy", 500)]


def test_market_buy_live_rejects_insufficient_jpy(monkeypatch):
    client = FakeClient(balance={"jpy": "499", "btc": "0"})
    service = OrderService(client)

    monkeypatch.setattr("app.order.order_service.settings", _settings(trading_enabled=True))
    monkeypatch.setattr("app.order.order_service.fetch_one", lambda *args, **kwargs: (0, 1, None))
    monkeypatch.setattr(service, "_ensure_no_recent_order", lambda side, purpose: None)

    with pytest.raises(OrderExecutionError):
        service.market_buy(500)

    assert client.market_buy_calls == []


def test_market_sell_live_clamps_to_available_balance(monkeypatch):
    client = FakeClient(balance={"jpy": "0", "btc": "0.003"})
    service = OrderService(client)

    monkeypatch.setattr("app.order.order_service.settings", _settings(trading_enabled=True))
    monkeypatch.setattr("app.order.order_service.fetch_one", lambda *args, **kwargs: (0, 1, None))
    monkeypatch.setattr(service, "_ensure_no_recent_order", lambda side, purpose: None)
    monkeypatch.setattr(service, "record_order", lambda *args, **kwargs: 12)

    result = service.market_sell(0.01)

    assert result.status == "SENT"
    assert client.market_sell_calls == [("btc_jpy", 0.003)]
