from __future__ import annotations

from app.backtest.historical_data_service import HistoricalDataService
from app.backtest.historical_trade_store import HistoricalTradeStore
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
    store = HistoricalTradeStore()
    inserted = store.save_trades(settings.symbol, trades)
    total = store.count(settings.symbol)
    started_at, ended_at = store.date_range(settings.symbol)

    print(f"api_trade_count={len(trades)}")
    print(f"inserted_count={inserted}")
    print(f"db_total_count={total}")
    if started_at and ended_at:
        print(f"db_range={started_at} -> {ended_at}")


if __name__ == "__main__":
    main()
