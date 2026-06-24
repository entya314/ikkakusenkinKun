import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
DB_DRIVER = DB_DRIVER.strip().strip("{}")

connection_string = (
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

tables = [
    "balances",
    "bot_status",
    "candles",
    "executions",
    "market_prices",
    "notifications",
    "orders",
    "positions",
    "risk_events",
    "settings",
    "signals",
    "system_logs",
    "trades",
]

try:
    with pyodbc.connect(connection_string, timeout=5) as conn:
        cursor = conn.cursor()

        print("テーブルSELECT確認開始")

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM dbo.{table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count}件")

        print("全テーブルSELECT成功")

except Exception as e:
    print("テーブルSELECT確認失敗")
    print(e)