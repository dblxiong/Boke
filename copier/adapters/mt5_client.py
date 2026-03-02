from __future__ import annotations

from dataclasses import dataclass, field

from copier.core.models import CopiedOrder


class OrderTarget:
    def send_order(self, order: CopiedOrder) -> str:
        raise NotImplementedError


@dataclass
class FakeMT5Client(OrderTarget):
    account_name: str
    sent_orders: list[CopiedOrder] = field(default_factory=list)

    def send_order(self, order: CopiedOrder) -> str:
        self.sent_orders.append(order)
        return f"fake-{len(self.sent_orders)}"


class MT5Client(OrderTarget):
    """Real MT5 adapter.

    Requires `pip install MetaTrader5` and a running terminal.
    """

    def __init__(self, login: int, password: str, server: str, path: str | None = None) -> None:
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise RuntimeError("MetaTrader5 package not installed") from exc

        self.mt5 = mt5
        if not self.mt5.initialize(path=path, login=login, password=password, server=server):
            raise RuntimeError(f"MT5 initialize failed: {self.mt5.last_error()}")

    def send_order(self, order: CopiedOrder) -> str:
        order_type = self.mt5.ORDER_TYPE_BUY if order.side.value == "BUY" else self.mt5.ORDER_TYPE_SELL
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": order.symbol,
            "volume": order.volume,
            "type": order_type,
            "deviation": 10,
            "comment": f"copied_from_{order.source_ticket}",
        }
        result = self.mt5.order_send(request)
        if result is None or result.retcode != self.mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"MT5 order failed: {result}")
        return str(result.order)
