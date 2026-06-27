from datetime import datetime, timedelta
from decimal import Decimal

from app.backtest.backtest_service import BacktestService, build_higher_timeframe_candles
from app.backtest.historical_candle_store import load_candles_from_csv
from app.market.candle_service import Candle


def _trend_candles(count: int = 360) -> list[Candle]:
    start = datetime(2026, 1, 1)
    candles = []
    for i in range(count):
        price = Decimal("1000000") + Decimal(i * 500)
        candles.append(
            Candle(
                symbol="BTC_JPY",
                timeframe="5m",
                open_price=price,
                high_price=price + Decimal("100"),
                low_price=price - Decimal("100"),
                close_price=price,
                volume=Decimal("0.1"),
                started_at=start + timedelta(minutes=5 * i),
                ended_at=start + timedelta(minutes=5 * (i + 1)),
            )
        )
    return candles


def test_build_higher_timeframe_candles_groups_15m():
    candles = build_higher_timeframe_candles(_trend_candles(6), "BTC_JPY", "15m")

    assert len(candles) == 2
    assert candles[0].open_price == Decimal("1000000")
    assert candles[0].close_price == Decimal("1001000")
    assert candles[0].volume == Decimal("0.3")


def test_backtest_runs_without_real_orders():
    result = BacktestService().run(
        candles_5m=_trend_candles(),
        candles_15m=None,
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


def test_load_candles_from_csv(tmp_path):
    csv_path = tmp_path / "candles.csv"
    csv_path.write_text(
        "started_at,open,high,low,close,volume\n"
        "2026-01-01 00:00:00,100,110,90,105,1.5\n",
        encoding="utf-8",
    )

    candles = load_candles_from_csv(csv_path, "BTC_JPY", "5m")

    assert len(candles) == 1
    assert candles[0].open_price == Decimal("100")
    assert candles[0].close_price == Decimal("105")
    assert candles[0].volume == Decimal("1.5")
