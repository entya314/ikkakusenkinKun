from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.backtest.backtest_service import BacktestService
from app.backtest.candle_builder import build_candles_from_trades
from app.backtest.historical_data_service import HistoricalDataService
from app.backtest.models import HistoricalTrade


def _trend_trades(count: int = 360) -> list[HistoricalTrade]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    trades = []
    for i in range(count):
        trades.append(
            HistoricalTrade(
                id=i + 1,
                price=Decimal("1000000") + Decimal(i * 500),
                amount=Decimal("0.01"),
                created_at=start + timedelta(minutes=i),
                side="buy" if i % 2 == 0 else "sell",
            )
        )
    return trades


def test_build_candles_from_trades_groups_5m():
    candles = build_candles_from_trades(_trend_trades(10), "BTC_JPY", "5m")

    assert len(candles) == 2
    assert candles[0].open_price == Decimal("1000000")
    assert candles[0].close_price == Decimal("1002000")
    assert candles[0].volume == Decimal("0.05")


def test_backtest_runs_without_real_orders():
    result = BacktestService().run(
        trades=_trend_trades(),
        symbol="BTC_JPY",
        strategy_name="sma_cross_only",
        initial_jpy=100000,
        order_amount_jpy=5000,
        take_profit_rate=0.005,
        stop_loss_rate=0.007,
    )

    assert result.strategy_name == "sma_cross_only"
    assert result.initial_jpy == Decimal("100000")
    assert result.trade_count >= 1
    assert result.final_jpy > Decimal("100000")


def test_historical_data_service_fetches_recent_trades_without_paging_params():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def get_trades(self, **kwargs):
            self.calls.append(kwargs)
            return {
                "success": True,
                "data": [
                    {
                        "id": 10,
                        "rate": "1000000",
                        "amount": "0.01",
                        "order_type": "buy",
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ],
            }

    client = FakeClient()
    trades = HistoricalDataService(client).fetch_recent_trades("btc_jpy", pages=10, limit=50)

    assert len(trades) == 1
    assert trades[0].id == 10
    assert client.calls == [{"pair": "btc_jpy", "limit": 50}]
