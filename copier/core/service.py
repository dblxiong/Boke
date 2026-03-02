from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from copier.adapters.mt5_client import OrderTarget
from copier.core.engine import CopierEngine
from copier.core.models import CopiedOrder, TradeEvent
from copier.storage.sqlite_store import SQLiteStore


@dataclass(slots=True)
class ProcessResult:
    copied_order: CopiedOrder | None
    target_ticket: str | None


class CopierService:
    def __init__(self, engine: CopierEngine, target: OrderTarget, store: SQLiteStore) -> None:
        self.engine = engine
        self.target = target
        self.store = store

    def start(self) -> None:
        self.store.initialize()
        self.engine.start()

    def stop(self) -> None:
        self.engine.stop()

    def process_event(self, event: TradeEvent) -> ProcessResult:
        copied = self.engine.on_event(event)
        if copied is None:
            self.store.log_event(event, "skipped", datetime.utcnow().isoformat())
            return ProcessResult(None, None)

        target_ticket = self.target.send_order(copied)
        self.store.save_mapping(event.ticket, target_ticket, copied.symbol)
        self.store.log_event(event, "copied", datetime.utcnow().isoformat())
        return ProcessResult(copied, target_ticket)
