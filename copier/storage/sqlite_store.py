from __future__ import annotations

import sqlite3
from pathlib import Path

from copier.core.models import TradeEvent


class SQLiteStore:
    def __init__(self, db_path: str = "copier.db") -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS order_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_ticket INTEGER NOT NULL,
                    target_ticket TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_ticket INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    logged_at TEXT NOT NULL
                )
                """
            )

    def save_mapping(self, source_ticket: int, target_ticket: str, symbol: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO order_mappings (source_ticket, target_ticket, symbol) VALUES (?, ?, ?)",
                (source_ticket, target_ticket, symbol),
            )

    def log_event(self, event: TradeEvent, status: str, ts: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO event_logs (source_ticket, symbol, action, status, logged_at) VALUES (?, ?, ?, ?, ?)",
                (event.ticket, event.symbol, event.action.value, status, ts),
            )

    def count_mappings(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM order_mappings").fetchone()
        return int(row[0])
