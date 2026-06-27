from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return float(value)


def _normalize_driver(driver: str) -> str:
    """ODBCドライバー名を接続文字列用に正規化する。"""
    return driver.strip().strip("{}")


@dataclass(frozen=True)
class Settings:
    # SQL Server
    db_driver: str = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    db_server: str = os.getenv("DB_SERVER", r"MSI\SQLEXPRESS")
    # 既存の .env に合わせて DB_NAME を優先する。
    # 互換用に DB_DATABASE も読めるようにしておく。
    db_database: str = os.getenv("DB_NAME") or os.getenv("DB_DATABASE", "CryptoBot")
    # windows / sqlserver のように指定する想定。未指定ならWindows認証。
    db_auth: str = os.getenv("DB_AUTH", "windows").strip().lower()
    db_username: str = os.getenv("DB_USERNAME", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_trust_server_certificate: str = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")
    db_encrypt: str = os.getenv("DB_ENCRYPT", "yes")

    # Coincheck API
    coincheck_base_url: str = os.getenv("COINCHECK_BASE_URL", "https://coincheck.com")
    coincheck_access_key: str = os.getenv("COINCHECK_ACCESS_KEY", "")
    coincheck_secret_key: str = os.getenv("COINCHECK_SECRET_KEY", "")

    # LINE Messaging API
    line_channel_access_token: str = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    line_user_id: str = os.getenv("LINE_USER_ID", "")

    # Bot basic settings
    exchange_name: str = os.getenv("EXCHANGE_NAME", "coincheck")
    symbol: str = os.getenv("SYMBOL", "BTC_JPY")
    base_symbol: str = os.getenv("BASE_SYMBOL", "BTC")
    quote_symbol: str = os.getenv("QUOTE_SYMBOL", "JPY")

    trading_enabled: bool = _get_bool("TRADING_ENABLED", False)
    order_amount_jpy: int = _get_int("ORDER_AMOUNT_JPY", 5000)
    take_profit_rate: float = _get_float("TAKE_PROFIT_RATE", 0.005)
    stop_loss_rate: float = _get_float("STOP_LOSS_RATE", 0.007)
    main_loop_interval_seconds: int = _get_int("MAIN_LOOP_INTERVAL_SECONDS", 60)
    strategy_name: str = os.getenv("STRATEGY_NAME", "sma_rsi_trend")

    # Backtest settings
    backtest_initial_jpy: int = _get_int("BACKTEST_INITIAL_JPY", 100000)
    backtest_order_amount_jpy: int = _get_int("BACKTEST_ORDER_AMOUNT_JPY", 5000)

    # Risk settings
    max_daily_loss_rate: float = _get_float("MAX_DAILY_LOSS_RATE", 0.03)
    max_consecutive_losses: int = _get_int("MAX_CONSECUTIVE_LOSSES", 3)
    api_retry_count: int = _get_int("API_RETRY_COUNT", 3)
    api_retry_interval_seconds: int = _get_int("API_RETRY_INTERVAL_SECONDS", 5)

    @property
    def db_connection_string(self) -> str:
        """
        SQL Server接続文字列を返す。

        現在の .env 想定:
            DB_DRIVER=ODBC Driver 17 for SQL Server
            DB_SERVER=MSI\\SQLEXPRESS
            DB_NAME=CryptoBot
            DB_AUTH=windows

        Windows認証の場合は UID/PWD を付けない。
        SQL Server認証にしたい場合は DB_AUTH=sqlserver にして、
        DB_USERNAME と DB_PASSWORD を .env に設定する。
        """
        driver = _normalize_driver(self.db_driver)

        parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={self.db_server}",
            f"DATABASE={self.db_database}",
            f"Encrypt={self.db_encrypt}",
            f"TrustServerCertificate={self.db_trust_server_certificate}",
        ]

        if self.db_auth in {"windows", "trusted", "integrated"}:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.db_username}")
            parts.append(f"PWD={self.db_password}")

        return ";".join(parts) + ";"


settings = Settings()
