from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.backtest.models import HistoricalTrade
from app.common.exceptions import ExchangeApiError
from app.exchange.exchange_client import CoincheckClient


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


class HistoricalDataService:
    def __init__(self, client: CoincheckClient) -> None:
        self.client = client

    def fetch_recent_trades(
        self,
        pair: str,
        pages: int = 5,
        limit: int = 100,
    ) -> list[HistoricalTrade]:
        all_trades: list[HistoricalTrade] = []
        ending_before: int | None = None

        for _ in range(pages):
            payload = self.client.get_trades(pair=pair, limit=limit, ending_before=ending_before)
            raw_trades = payload.get("data") if isinstance(payload, dict) else None
            if not raw_trades:
                break

            parsed = [self._parse_trade(item) for item in raw_trades]
            all_trades.extend(parsed)
            oldest_id = min(item.id for item in parsed)
            if ending_before == oldest_id:
                break
            ending_before = oldest_id

        unique = {trade.id: trade for trade in all_trades}
        return sorted(unique.values(), key=lambda item: item.created_at)

    def _parse_trade(self, item: dict[str, Any]) -> HistoricalTrade:
        try:
            return HistoricalTrade(
                id=int(item["id"]),
                price=Decimal(str(item["rate"])),
                amount=Decimal(str(item["amount"])),
                created_at=_parse_datetime(str(item["created_at"])),
                side=item.get("order_type"),
            )
        except KeyError as exc:
            raise ExchangeApiError(f"取引履歴の形式が想定外です: {item}") from exc
