from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.database.db import execute, fetch_all, fetch_one
from config import settings


@dataclass(frozen=True)
class RiskResult:
    can_trade: bool
    reason: str


class RiskService:
    def check_emergency_stop(self) -> RiskResult:
        status_result = self._check_bot_status()
        if not status_result.can_trade:
            return status_result

        loss_result = self._check_daily_loss_limit()
        if not loss_result.can_trade:
            return loss_result

        consecutive_result = self._check_consecutive_loss_limit()
        if not consecutive_result.can_trade:
            return consecutive_result

        return RiskResult(True, "Trading is allowed.")

    def record_risk_event(self, event_type: str, severity: str, message: str, action_taken: str | None = None) -> None:
        execute(
            """
            INSERT INTO dbo.risk_events (event_type, severity, message, action_taken)
            VALUES (?, ?, ?, ?)
            """,
            [event_type, severity, message, action_taken],
        )

    def _check_bot_status(self) -> RiskResult:
        row = fetch_one(
            """
            SELECT TOP 1 emergency_stop, is_trading_enabled, reason
            FROM dbo.bot_status
            ORDER BY id DESC
            """
        )
        if row is None:
            return RiskResult(False, "bot_status is missing.")
        emergency_stop, is_trading_enabled, reason = row
        if emergency_stop:
            return RiskResult(False, f"Emergency stop is enabled: {reason}")
        if not is_trading_enabled:
            return RiskResult(False, "DB bot_status.is_trading_enabled is off.")
        return RiskResult(True, "Bot status is enabled.")

    def _check_daily_loss_limit(self) -> RiskResult:
        row = fetch_one(
            """
            SELECT COALESCE(SUM(net_profit_jpy), 0)
            FROM dbo.trades
            WHERE symbol = ? AND CAST(closed_at AS date) = CAST(SYSDATETIME() AS date)
            """,
            [settings.symbol],
        )
        daily_profit = Decimal(str(row[0] if row else "0"))
        loss_limit = Decimal(str(settings.max_daily_loss_jpy))
        if daily_profit < -loss_limit:
            return RiskResult(False, f"Daily loss limit reached: {daily_profit} JPY.")
        return RiskResult(True, "Daily loss is within limit.")

    def _check_consecutive_loss_limit(self) -> RiskResult:
        rows = fetch_all(
            """
            SELECT TOP (?) net_profit_jpy
            FROM dbo.trades
            WHERE symbol = ?
            ORDER BY closed_at DESC
            """,
            [settings.max_consecutive_losses, settings.symbol],
        )
        if len(rows) < settings.max_consecutive_losses:
            return RiskResult(True, "Consecutive loss count is within limit.")
        if all(Decimal(str(row[0])) < 0 for row in rows):
            return RiskResult(False, f"Consecutive loss limit reached: {settings.max_consecutive_losses}.")
        return RiskResult(True, "Consecutive loss count is within limit.")
