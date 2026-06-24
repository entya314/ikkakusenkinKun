import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

# プロジェクト直下の .env を読む
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

connection_string = (
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

try:
    with pyodbc.connect(connection_string, timeout=5) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT @@SERVERNAME, DB_NAME(), GETDATE()")
        row = cursor.fetchone()

        print("DB接続成功")
        print(f"サーバー名: {row[0]}")
        print(f"DB名: {row[1]}")
        print(f"現在時刻: {row[2]}")

except Exception as e:
    print("DB接続失敗")
    print(e)

cursor.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_SCHEMA, TABLE_NAME
""")

tables = cursor.fetchall()

print("\n登録済みテーブル一覧:")
for schema, table in tables:
    print(f"- {schema}.{table}")