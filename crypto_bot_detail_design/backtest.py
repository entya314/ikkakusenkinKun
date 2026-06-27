from __future__ import annotations

from app.backtest.backtest_service import BacktestService
from app.backtest.historical_data_service import HistoricalDataService
from app.exchange.exchange_client import CoincheckClient
from config import settings


def main() -> None:
    client = CoincheckClient()
    history = HistoricalDataService(client)
    trades = history.fetch_recent_trades(
        pair=settings.symbol.lower(),
        pages=settings.backtest_trade_pages,
        limit=settings.backtest_trade_limit,
    )
    result = BacktestService().run(
        trades=trades,
        symbol=settings.symbol,
        strategy_name=settings.strategy_name,
        initial_jpy=settings.backtest_initial_jpy,
        order_amount_jpy=settings.backtest_order_amount_jpy,
    )

    print(f"strategy={result.strategy_name}")
    print(f"symbol={result.symbol}")
    print(f"trades_source_count={len(trades)}")
    print(f"initial_jpy={result.initial_jpy:.0f}")
    print(f"final_jpy={result.final_jpy:.0f}")
    print(f"total_profit_jpy={result.total_profit_jpy:.0f}")
    print(f"total_return_rate={result.total_return_rate * 100:.2f}%")
    print(f"trade_count={result.trade_count}")
    print(f"win_rate={result.win_rate * 100:.2f}%")
    print(f"max_drawdown_jpy={result.max_drawdown_jpy:.0f}")
    print(f"max_drawdown_rate={result.max_drawdown_rate * 100:.2f}%")
    print(f"max_consecutive_losses={result.max_consecutive_losses}")


if __name__ == "__main__":
    main()
