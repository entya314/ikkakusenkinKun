from __future__ import annotations

from app.strategy.signal_service import IndicatorResult
from app.strategy.strategies import StrategyDecision, TradeAction, get_strategy
from config import settings


class StrategyService:
    def __init__(self, strategy_name: str | None = None) -> None:
        self.strategy = get_strategy(strategy_name or settings.strategy_name)

    def should_buy(
        self,
        indicators_5m: IndicatorResult,
        indicators_15m: IndicatorResult,
        has_open_position: bool,
    ) -> StrategyDecision:
        return self.strategy.should_buy(indicators_5m, indicators_15m, has_open_position)

    def judge_exit(
        self,
        entry_price: float,
        current_price: float,
        take_profit_rate: float,
        stop_loss_rate: float,
    ) -> StrategyDecision:
        return self.strategy.judge_exit(entry_price, current_price, take_profit_rate, stop_loss_rate)
