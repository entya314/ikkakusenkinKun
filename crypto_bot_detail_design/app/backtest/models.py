from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class BacktestTrade:
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    amount: Decimal
    gross_profit_jpy: Decimal
    profit_rate: Decimal
    exit_reason: str


@dataclass(frozen=True)
class BacktestResult:
    strategy_name: str
    symbol: str
    initial_jpy: Decimal
    final_jpy: Decimal
    total_profit_jpy: Decimal
    total_return_rate: Decimal
    trade_count: int
    win_count: int
    loss_count: int
    win_rate: Decimal
    max_drawdown_jpy: Decimal
    max_drawdown_rate: Decimal
    max_consecutive_losses: int
    trades: list[BacktestTrade]
