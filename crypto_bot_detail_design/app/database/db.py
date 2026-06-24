from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable

import pyodbc

from config import settings


@contextmanager
def get_connection():
    conn = pyodbc.connect(settings.db_connection_string)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(sql: str, params: Iterable[Any] | None = None) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params or []))


def fetch_one(sql: str, params: Iterable[Any] | None = None) -> Any | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params or []))
        return cursor.fetchone()


def fetch_all(sql: str, params: Iterable[Any] | None = None) -> list[Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params or []))
        return cursor.fetchall()
