from pathlib import Path

from copier.adapters.mt5_client import FakeMT5Client
from copier.core.engine import CopierEngine
from copier.core.models import ActionType, CopierRule, OrderSide, RiskLimits, TradeEvent
from copier.core.service import CopierService
from copier.storage.sqlite_store import SQLiteStore


def test_forward_copy_with_ratio() -> None:
    engine = CopierEngine(CopierRule(reverse=False, lot_ratio=2.0))
    engine.start()

    event = TradeEvent(
        ticket=1,
        symbol="EURUSD",
        side=OrderSide.BUY,
        volume=0.1,
        magic=100,
        floating_profit=12,
        action=ActionType.OPEN,
    )

    copied = engine.on_event(event)
    assert copied is not None
    assert copied.side == OrderSide.BUY
    assert copied.volume == 0.2


def test_reverse_copy_with_fixed_lot_and_magic_filter() -> None:
    engine = CopierEngine(CopierRule(reverse=True, fixed_lot=0.05, allowed_magics={777}))
    engine.start()

    blocked_event = TradeEvent(
        ticket=2,
        symbol="XAUUSD",
        side=OrderSide.SELL,
        volume=1.0,
        magic=123,
        floating_profit=20,
        action=ActionType.OPEN,
    )
    assert engine.on_event(blocked_event) is None

    allowed_event = TradeEvent(
        ticket=3,
        symbol="XAUUSD",
        side=OrderSide.SELL,
        volume=1.0,
        magic=777,
        floating_profit=20,
        action=ActionType.OPEN,
    )

    copied = engine.on_event(allowed_event)
    assert copied is not None
    assert copied.side == OrderSide.BUY
    assert copied.volume == 0.05


def test_risk_limits_block_extra_orders() -> None:
    engine = CopierEngine(
        CopierRule(lot_ratio=1.0),
        risk_limits=RiskLimits(max_open_orders=1, max_total_volume=0.2),
    )
    engine.start()

    first = TradeEvent(1, "EURUSD", OrderSide.BUY, 0.1, 100, 0.0, ActionType.OPEN)
    second = TradeEvent(2, "EURUSD", OrderSide.BUY, 0.2, 100, 0.0, ActionType.OPEN)

    assert engine.on_event(first) is not None
    assert engine.on_event(second) is None


def test_service_persists_mappings_and_logs(tmp_path: Path) -> None:
    db_file = tmp_path / "test.db"
    store = SQLiteStore(str(db_file))
    target = FakeMT5Client("target")
    engine = CopierEngine(CopierRule())
    service = CopierService(engine=engine, target=target, store=store)
    service.start()

    event = TradeEvent(7, "EURUSD", OrderSide.BUY, 0.1, 100, 10.0, ActionType.OPEN)
    result = service.process_event(event)

    assert result.copied_order is not None
    assert result.target_ticket == "fake-1"
    assert store.count_mappings() == 1
