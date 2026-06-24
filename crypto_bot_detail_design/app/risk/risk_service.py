from __future__ import annotations

from dataclasses import dataclass

from app.database.db import execute, fetch_one
from config import settings


@dataclass(frozen=True)
class RiskResult:
    can_trade: bool
    reason: str


class RiskService:
    def check_emergency_stop(self) -> RiskResult:
        row = fetch_one(
            """
            SELECT TOP 1 emergency_stop, is_trading_enabled, reason
            FROM dbo.bot_status
            ORDER BY id DESC
            """
        )
        if row is None:
            return RiskResult(False, "bot_statusが未作成")
        emergency_stop, is_trading_enabled, reason = row
        if emergency_stop:
            return RiskResult(False, f"緊急停止中: {reason}")
        if not is_trading_enabled:
            return RiskResult(False, "DB上で自動売買が無効")
        return RiskResult(True, "取引可能")

    def record_risk_event(self, event_type: str, severity: str, message: str, action_taken: str | None = None) -> None:
        execute(
            """
            INSERT INTO dbo.risk_events (event_type, severity, message, action_taken)
            VALUES (?, ?, ?, ?)
            """,
            [event_type, severity, message, action_taken],
        )
