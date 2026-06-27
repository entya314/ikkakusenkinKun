from __future__ import annotations

from decimal import Decimal

from app.backtest.candle_builder import build_candles_from_trades
from app.backtest.models import BacktestResult, BacktestTrade, HistoricalTrade
from app.market.candle_service import Candle
from app.strategy.signal_service import SignalService
from app.strategy.strategies import TradeAction, get_strategy
from config import settings


class BacktestService:
    def __init__(self) -> None:
        self.signal_service = SignalService()

    def run(
        self,
        trades: list[HistoricalTrade],
        symbol: str,
        strategy_name: str,
        initial_jpy: int | Decimal | None = None,
        order_amount_jpy: int | Decimal | None = None,
        take_profit_rate: float | None = None,
        stop_loss_rate: float | None = None,
    ) -> BacktestResult:
        strategy = get_strategy(strategy_name)
        initial_cash = Decimal(str(initial_jpy if initial_jpy is not None else settings.backtest_initial_jpy))
        order_cash = Decimal(str(order_amount_jpy if order_amount_jpy is not None else settings.backtest_order_amount_jpy))
        take_profit = take_profit_rate if take_profit_rate is not None else settings.take_profit_rate
        stop_loss = stop_loss_rate if stop_loss_rate is not None else settings.stop_loss_rate

        candles_5m = build_candles_from_trades(trades, symbol, "5m")
        candles_15m = build_candles_from_trades(trades, symbol, "15m")

        cash = initial_cash
        position_amount = Decimal("0")
        entry_price: Decimal | None = None
        entry_time = None
        completed_trades: list[BacktestTrade] = []
        peak_equity = initial_cash
        max_drawdown = Decimal("0")
        consecutive_losses = 0
        max_consecutive_losses = 0

        for index, candle in enumerate(candles_5m):
            current_price = candle.close_price
            current_equity = cash + position_amount * current_price
            if current_equity > peak_equity:
                peak_equity = current_equity
            drawdown = peak_equity - current_equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown

            if position_amount > 0 and entry_price is not None and entry_time is not None:
                exit_decision = strategy.judge_exit(
                    float(entry_price),
                    float(current_price),
                    take_profit,
                    stop_loss,
                )
                if exit_decision.action in {TradeAction.SELL_TAKE_PROFIT, TradeAction.SELL_STOP_LOSS}:
                    exit_value = position_amount * current_price
                    gross_profit = exit_value - (position_amount * entry_price)
                    cash += exit_value
                    trade = BacktestTrade(
                        entry_time=entry_time,
                        exit_time=candle.ended_at,
                        entry_price=entry_price,
                        exit_price=current_price,
                        amount=position_amount,
                        gross_profit_jpy=gross_profit,
                        profit_rate=(current_price - entry_price) / entry_price,
                        exit_reason=exit_decision.reason,
                    )
                    completed_trades.append(trade)
                    if gross_profit < 0:
                        consecutive_losses += 1
                        max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                    else:
                        consecutive_losses = 0
                    position_amount = Decimal("0")
                    entry_price = None
                    entry_time = None
                    continue

            if position_amount == 0 and cash >= order_cash:
                indicators_5m = self.signal_service.calculate_indicators(_closes(candles_5m[: index + 1]))
                indicators_15m = self.signal_service.calculate_indicators(
                    _closes([item for item in candles_15m if item.ended_at <= candle.ended_at])
                )
                buy_decision = strategy.should_buy(indicators_5m, indicators_15m, has_open_position=False)
                if buy_decision.action == TradeAction.BUY:
                    position_amount = order_cash / current_price
                    cash -= order_cash
                    entry_price = current_price
                    entry_time = candle.ended_at

        if position_amount > 0 and entry_price is not None and entry_time is not None and candles_5m:
            last = candles_5m[-1]
            exit_value = position_amount * last.close_price
            gross_profit = exit_value - (position_amount * entry_price)
            cash += exit_value
            completed_trades.append(
                BacktestTrade(
                    entry_time=entry_time,
                    exit_time=last.ended_at,
                    entry_price=entry_price,
                    exit_price=last.close_price,
                    amount=position_amount,
                    gross_profit_jpy=gross_profit,
                    profit_rate=(last.close_price - entry_price) / entry_price,
                    exit_reason="バックテスト終了時に評価決済",
                )
            )

        final_jpy = cash
        total_profit = final_jpy - initial_cash
        wins = [trade for trade in completed_trades if trade.gross_profit_jpy >= 0]
        losses = [trade for trade in completed_trades if trade.gross_profit_jpy < 0]
        trade_count = len(completed_trades)
        win_rate = Decimal(len(wins)) / Decimal(trade_count) if trade_count else Decimal("0")
        max_drawdown_rate = max_drawdown / peak_equity if peak_equity else Decimal("0")

        return BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            initial_jpy=initial_cash,
            final_jpy=final_jpy,
            total_profit_jpy=total_profit,
            total_return_rate=total_profit / initial_cash if initial_cash else Decimal("0"),
            trade_count=trade_count,
            win_count=len(wins),
            loss_count=len(losses),
            win_rate=win_rate,
            max_drawdown_jpy=max_drawdown,
            max_drawdown_rate=max_drawdown_rate,
            max_consecutive_losses=max_consecutive_losses,
            trades=completed_trades,
        )


def _closes(candles: list[Candle]) -> list[float]:
    return [float(candle.close_price) for candle in candles]
