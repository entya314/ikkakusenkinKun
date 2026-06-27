from __future__ import annotations

import argparse

from app.backtest.historical_candle_store import HistoricalCandleStore
from config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="CSVローソク足をDBへ取り込みます。")
    parser.add_argument("csv_path", help="CSVファイルパス")
    parser.add_argument("--symbol", default=settings.symbol, help="銘柄。例: BTC_JPY")
    parser.add_argument("--timeframe", default="5m", help="時間足。例: 5m")
    args = parser.parse_args()

    store = HistoricalCandleStore()
    inserted = store.import_csv(args.csv_path, args.symbol, args.timeframe)
    total = store.count(args.symbol, args.timeframe)
    started_at, ended_at = store.date_range(args.symbol, args.timeframe)

    print(f"inserted_count={inserted}")
    print(f"db_total_count={total}")
    if started_at and ended_at:
        print(f"db_range={started_at} -> {ended_at}")


if __name__ == "__main__":
    main()
