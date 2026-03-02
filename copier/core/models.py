from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class ActionType(str, Enum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"


@dataclass(slots=True)
class TradeEvent:
    ticket: int
    symbol: str
    side: OrderSide
    volume: float
    magic: int
    floating_profit: float
    action: ActionType
    close_ratio: float = 1.0


@dataclass(slots=True)
class CopierRule:
    reverse: bool = False
    fixed_lot: float | None = None
    lot_ratio: float = 1.0
    allowed_magics: set[int] | None = None
    min_profit_trigger: float | None = None
    max_loss_trigger: float | None = None

    def can_copy(self, event: TradeEvent) -> bool:
        if self.allowed_magics and event.magic not in self.allowed_magics:
            return False

        if self.min_profit_trigger is not None and event.floating_profit < self.min_profit_trigger:
            return False

        if self.max_loss_trigger is not None and event.floating_profit > -abs(self.max_loss_trigger):
            return False

        return True

    def target_volume(self, source_volume: float) -> float:
        if self.fixed_lot is not None:
            return max(round(self.fixed_lot, 2), 0.01)
        return max(round(source_volume * self.lot_ratio, 2), 0.01)

    def target_side(self, side: OrderSide) -> OrderSide:
        if not self.reverse:
            return side
        return OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY


@dataclass(slots=True)
class CopiedOrder:
    source_ticket: int
    symbol: str
    side: OrderSide
    volume: float
    action: ActionType
    close_ratio: float = 1.0


@dataclass(slots=True)
class RiskLimits:
    max_open_orders: int = 20
    max_total_volume: float = 5.0
