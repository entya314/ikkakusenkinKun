from __future__ import annotations

import time
from decimal import Decimal

from app.common.logger import setup_logger
from app.exchange.exchange_client import CoincheckClient
from app.market.candle_service import CandleService
from app.market.market_data_service import MarketDataService
from app.notification.line_notifier import LineNotifier
from app.order.order_service import OrderService
from app.position.position_service import PositionService
from app.risk.risk_service import RiskService
from app.strategy.signal_service import SignalService
from app.strategy.strategy_service import StrategyService
from app.strategy.strategies import TradeAction
from config import settings


logger = setup_logger()


def run_once() -> None:
    client = CoincheckClient()
    market_data_service = MarketDataService(client)
    candle_service = CandleService()
    signal_service = SignalService()
    strategy_service = StrategyService()
    order_service = OrderService(client)
    position_service = PositionService()
    risk_service = RiskService()

    current_price: Decimal = market_data_service.collect_current_price()
    logger.info("Current price collected: %s %s", settings.symbol, current_price)

    candle_service.build_from_market_prices(settings.symbol, "5m")
    candle_service.build_from_market_prices(settings.symbol, "15m")
    candles_5m = candle_service.get_recent_candles(settings.symbol, "5m", limit=120)
    candles_15m = candle_service.get_recent_candles(settings.symbol, "15m", limit=120)
    if len(candles_5m) < 20 or len(candles_15m) < 20:
        logger.info("Trading skipped: not enough candles. 5m=%s 15m=%s", len(candles_5m), len(candles_15m))
        return

    risk_result = risk_service.check_emergency_stop()
    if not risk_result.can_trade:
        logger.info("Trading skipped after data collection: %s", risk_result.reason)
        return

    open_position = position_service.get_open_position()
    if open_position is not None:
        _handle_open_position(open_position, current_price, strategy_service, order_service, position_service)
        return

    indicators_5m = signal_service.calculate_indicators([float(candle.close_price) for candle in candles_5m])
    indicators_15m = signal_service.calculate_indicators([float(candle.close_price) for candle in candles_15m])
    decision = strategy_service.should_buy(indicators_5m, indicators_15m, has_open_position=False)
    logger.info("Buy decision: %s / %s", decision.action.value, decision.reason)
    if decision.action != TradeAction.BUY:
        return

    order_result = order_service.market_buy(settings.order_amount_jpy)
    entry_amount = Decimal(settings.order_amount_jpy) / current_price
    position_service.open_position(
        entry_order_id=order_result.order_id,
        entry_price=current_price,
        amount=entry_amount,
        take_profit_price=current_price * (Decimal("1") + Decimal(str(settings.take_profit_rate))),
        stop_loss_price=current_price * (Decimal("1") - Decimal(str(settings.stop_loss_rate))),
    )
    logger.info(
        "Buy order recorded: order_id=%s status=%s estimated_amount=%s",
        order_result.order_id,
        order_result.status,
        entry_amount,
    )


def _handle_open_position(
    open_position,
    current_price: Decimal,
    strategy_service: StrategyService,
    order_service: OrderService,
    position_service: PositionService,
) -> None:
    position_id = int(open_position[0])
    entry_price = Decimal(str(open_position[2]))
    amount = Decimal(str(open_position[3]))
    decision = strategy_service.judge_exit(
        entry_price=float(entry_price),
        current_price=float(current_price),
        take_profit_rate=settings.take_profit_rate,
        stop_loss_rate=settings.stop_loss_rate,
    )
    logger.info("Exit decision: %s / %s", decision.action.value, decision.reason)
    if decision.action not in {TradeAction.SELL_TAKE_PROFIT, TradeAction.SELL_STOP_LOSS}:
        return

    purpose = "TAKE_PROFIT" if decision.action == TradeAction.SELL_TAKE_PROFIT else "STOP_LOSS"
    order_result = order_service.market_sell(amount, purpose=purpose)
    position_service.close_position(position_id, order_result.order_id, exit_price=current_price, exit_reason=purpose)
    logger.info("Sell order recorded: order_id=%s status=%s", order_result.order_id, order_result.status)


def main() -> None:
    logger.info("IkkakusenkinKun started.")

    notifier = LineNotifier()
    notifier.send_text("IkkakusenkinKun started.", "SYSTEM_START")

    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            logger.info("Stopped by keyboard interrupt.")
            break
        except Exception as e:
            logger.exception("Main loop error: %s", e)

        time.sleep(settings.main_loop_interval_seconds)


if __name__ == "__main__":
    main()
