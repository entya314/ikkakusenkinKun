from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndicatorResult:
    sma_short: float | None
    sma_long: float | None
    rsi: float | None
    macd: float | None
    macd_signal: float | None


class SignalService:
    def calculate_sma(self, values: list[float], period: int) -> float | None:
        if len(values) < period:
            return None
        return sum(values[-period:]) / period

    def calculate_rsi(self, values: list[float], period: int = 14) -> float | None:
        if len(values) <= period:
            return None

        gains: list[float] = []
        losses: list[float] = []
        for i in range(-period, 0):
            diff = values[i] - values[i - 1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(diff))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def calculate_ema(self, values: list[float], period: int) -> float | None:
        if len(values) < period:
            return None
        k = 2 / (period + 1)
        ema = sum(values[:period]) / period
        for value in values[period:]:
            ema = value * k + ema * (1 - k)
        return ema

    def calculate_macd(self, values: list[float]) -> tuple[float | None, float | None]:
        if len(values) < 35:
            return None, None
        ema12 = self.calculate_ema(values, 12)
        ema26 = self.calculate_ema(values, 26)
        if ema12 is None or ema26 is None:
            return None, None
        macd = ema12 - ema26
        # 雛形ではsignal線を簡易扱い。実装時はMACD系列からEMA9を作る。
        macd_signal = macd
        return macd, macd_signal

    def calculate_indicators(self, close_prices: list[float]) -> IndicatorResult:
        macd, macd_signal = self.calculate_macd(close_prices)
        return IndicatorResult(
            sma_short=self.calculate_sma(close_prices, 5),
            sma_long=self.calculate_sma(close_prices, 20),
            rsi=self.calculate_rsi(close_prices),
            macd=macd,
            macd_signal=macd_signal,
        )
