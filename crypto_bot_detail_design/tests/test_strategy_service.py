from app.strategy.signal_service import IndicatorResult
from app.strategy.strategy_service import StrategyService, TradeAction


def test_should_buy_when_trend_up_and_rsi_ok():
    service = StrategyService()
    ind = IndicatorResult(sma_short=110, sma_long=100, rsi=55, macd=1, macd_signal=1)
    decision = service.should_buy(ind, ind, has_open_position=False)
    assert decision.action == TradeAction.BUY


def test_should_hold_when_has_open_position():
    service = StrategyService()
    ind = IndicatorResult(sma_short=110, sma_long=100, rsi=55, macd=1, macd_signal=1)
    decision = service.should_buy(ind, ind, has_open_position=True)
    assert decision.action == TradeAction.HOLD
