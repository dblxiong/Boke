from __future__ import annotations

from dataclasses import dataclass

from copier.core.models import ActionType, CopiedOrder, CopierRule, RiskLimits, TradeEvent


@dataclass(slots=True)
class EngineState:
    open_orders: int = 0
    total_volume: float = 0.0


class CopierEngine:
    def __init__(self, rule: CopierRule, risk_limits: RiskLimits | None = None) -> None:
        self.rule = rule
        self.risk_limits = risk_limits or RiskLimits()
        self.state = EngineState()
        self.running = False

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def on_event(self, event: TradeEvent) -> CopiedOrder | None:
        if not self.running:
            return None

        if not self.rule.can_copy(event):
            return None

        copied = CopiedOrder(
            source_ticket=event.ticket,
            symbol=event.symbol,
            side=self.rule.target_side(event.side),
            volume=self.rule.target_volume(event.volume),
            action=event.action,
            close_ratio=event.close_ratio if event.action == ActionType.PARTIAL_CLOSE else 1.0,
        )

        if not self._allowed_by_risk(copied):
            return None

        self._apply_state(copied)
        return copied

    def _allowed_by_risk(self, copied: CopiedOrder) -> bool:
        if copied.action == ActionType.OPEN:
            if self.state.open_orders + 1 > self.risk_limits.max_open_orders:
                return False
            if self.state.total_volume + copied.volume > self.risk_limits.max_total_volume:
                return False
        return True

    def _apply_state(self, copied: CopiedOrder) -> None:
        if copied.action == ActionType.OPEN:
            self.state.open_orders += 1
            self.state.total_volume = round(self.state.total_volume + copied.volume, 2)
        elif copied.action == ActionType.CLOSE and self.state.open_orders > 0:
            self.state.open_orders -= 1
            self.state.total_volume = max(round(self.state.total_volume - copied.volume, 2), 0.0)
        elif copied.action == ActionType.PARTIAL_CLOSE:
            reduced = round(copied.volume * copied.close_ratio, 2)
            self.state.total_volume = max(round(self.state.total_volume - reduced, 2), 0.0)
