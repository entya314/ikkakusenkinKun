class CryptoBotError(Exception):
    """一攫千金くん共通例外。"""


class ExchangeApiError(CryptoBotError):
    """取引所API関連エラー。"""


class OrderExecutionError(CryptoBotError):
    """注文実行関連エラー。"""


class RiskStopError(CryptoBotError):
    """リスク条件による停止。"""
