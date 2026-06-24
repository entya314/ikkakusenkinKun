from app.strategy.signal_service import SignalService


def test_calculate_sma():
    service = SignalService()
    assert service.calculate_sma([1, 2, 3, 4, 5], 5) == 3


def test_calculate_rsi_returns_value():
    service = SignalService()
    values = [1, 2, 3, 2, 4, 5, 4, 6, 7, 8, 7, 9, 10, 11, 12]
    result = service.calculate_rsi(values)
    assert result is not None
    assert 0 <= result <= 100
