from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any

import pymysql
from pymysql.cursors import DictCursor


DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "ceas")


def db_config(include_database: bool = True) -> dict[str, Any]:
    config: dict[str, Any] = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "cursorclass": DictCursor,
        "autocommit": False,
    }
    if include_database:
        config["database"] = DB_NAME
    return config


@contextmanager
def get_db(include_database: bool = True):
    connection = pymysql.connect(**db_config(include_database=include_database))
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def fetch_one_dict(connection, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()


def fetch_all_dicts(connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return list(cursor.fetchall())


def execute(connection, query: str, params: tuple[Any, ...] = ()) -> int:
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.lastrowid


def execute_many(connection, query: str, params: list[tuple[Any, ...]]) -> None:
    with connection.cursor() as cursor:
        cursor.executemany(query, params)


def log_activity(
    connection,
    event_type: str,
    user_id: int | None = None,
    culture_id: int | None = None,
    scenario_id: int | None = None,
    detail: str | None = None,
) -> None:
    execute(
        connection,
        """
        INSERT INTO activity_logs (user_id, event_type, culture_id, scenario_id, detail)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, event_type, culture_id, scenario_id, detail),
    )
