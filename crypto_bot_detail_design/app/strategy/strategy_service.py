from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.strategy.signal_service import IndicatorResult


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL_TAKE_PROFIT = "SELL_TAKE_PROFIT"
    SELL_STOP_LOSS = "SELL_STOP_LOSS"
    HOLD = "HOLD"
    STOP = "STOP"


@dataclass(frozen=True)
class StrategyDecision:
    action: TradeAction
    reason: str


class StrategyService:
    def should_buy(
        self,
        indicators_5m: IndicatorResult,
        indicators_15m: IndicatorResult,
        has_open_position: bool,
    ) -> StrategyDecision:
        if has_open_position:
            return StrategyDecision(TradeAction.HOLD, "既にポジションを保有している")

        required_values = [
            indicators_5m.sma_short,
            indicators_5m.sma_long,
            indicators_15m.sma_short,
            indicators_15m.sma_long,
            indicators_5m.rsi,
        ]
        if any(v is None for v in required_values):
            return StrategyDecision(TradeAction.HOLD, "指標計算に必要なデータが不足")

        trend_5m = indicators_5m.sma_short > indicators_5m.sma_long
        trend_15m = indicators_15m.sma_short > indicators_15m.sma_long
        rsi_ok = indicators_5m.rsi < 70

        if trend_5m and trend_15m and rsi_ok:
            return StrategyDecision(TradeAction.BUY, "5分足・15分足が上向き、RSI過熱なし")

        return StrategyDecision(TradeAction.HOLD, "買い条件未達")

    def judge_exit(
        self,
        entry_price: float,
        current_price: float,
        take_profit_rate: float,
        stop_loss_rate: float,
    ) -> StrategyDecision:
        take_profit_price = entry_price * (1 + take_profit_rate)
        stop_loss_price = entry_price * (1 - stop_loss_rate)

        if current_price >= take_profit_price:
            return StrategyDecision(TradeAction.SELL_TAKE_PROFIT, "利確条件到達")
        if current_price <= stop_loss_price:
            return StrategyDecision(TradeAction.SELL_STOP_LOSS, "損切り条件到達")
        return StrategyDecision(TradeAction.HOLD, "決済条件未達")
