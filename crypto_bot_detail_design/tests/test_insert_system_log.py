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

try:
    with pyodbc.connect(connection_string, timeout=5) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO dbo.system_logs (
                log_level,
                category,
                message,
                detail,
                created_at
            )
            VALUES (?, ?, ?, ?, GETDATE())
        """, (
            "INFO",
            "db_test",
            "DB INSERT test from Python",
            "Pythonからsystem_logsへのINSERT確認"
        ))

        conn.commit()

        print("system_logs INSERT成功")

        cursor.execute("""
            SELECT TOP 5
                id,
                log_level,
                category,
                message,
                detail,
                created_at
            FROM dbo.system_logs
            ORDER BY id DESC
        """)

        rows = cursor.fetchall()

        print("\n最新ログ:")
        for row in rows:
            print(row)

except Exception as e:
    print("system_logs INSERT失敗")
    print(e)