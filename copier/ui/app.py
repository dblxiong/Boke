from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk

from copier.adapters.mt5_client import FakeMT5Client
from copier.core.engine import CopierEngine
from copier.core.models import ActionType, CopierRule, OrderSide, RiskLimits, TradeEvent
from copier.core.service import CopierService
from copier.storage.sqlite_store import SQLiteStore


class CopierApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MT5 跟单工具")
        self.geometry("560x390")

        self.target = FakeMT5Client(account_name="target-demo")
        self.store = SQLiteStore("copier.db")
        self.service = self._build_service()

        self.status_var = tk.StringVar(value="状态：已停止")
        self.result_var = tk.StringVar(value="最近结果：无")

        self._build_widgets()

    def _build_service(self) -> CopierService:
        rule = CopierRule(
            reverse=False,
            fixed_lot=None,
            lot_ratio=1.0,
            allowed_magics=None,
            min_profit_trigger=None,
            max_loss_trigger=None,
        )
        engine = CopierEngine(rule=rule, risk_limits=RiskLimits(max_open_orders=20, max_total_volume=5.0))
        return CopierService(engine=engine, target=self.target, store=self.store)

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Label(frame, text="跟单规则").grid(row=0, column=0, sticky="w")

        self.reverse_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="反向跟单", variable=self.reverse_var).grid(row=1, column=0, sticky="w")

        ttk.Label(frame, text="固定手数(可空)").grid(row=2, column=0, sticky="w")
        self.fixed_lot_entry = ttk.Entry(frame)
        self.fixed_lot_entry.grid(row=2, column=1, sticky="ew")

        ttk.Label(frame, text="比例手数").grid(row=3, column=0, sticky="w")
        self.ratio_entry = ttk.Entry(frame)
        self.ratio_entry.insert(0, "1.0")
        self.ratio_entry.grid(row=3, column=1, sticky="ew")

        ttk.Label(frame, text="Magic白名单(逗号分隔)").grid(row=4, column=0, sticky="w")
        self.magic_entry = ttk.Entry(frame)
        self.magic_entry.grid(row=4, column=1, sticky="ew")

        ttk.Button(frame, text="应用规则", command=self.apply_rules).grid(row=5, column=0, pady=8, sticky="w")
        ttk.Button(frame, text="启动", command=self.start_service).grid(row=5, column=1, pady=8, sticky="w")
        ttk.Button(frame, text="停止", command=self.stop_service).grid(row=5, column=1, pady=8, sticky="e")
        ttk.Button(frame, text="模拟一笔信号", command=self.simulate_event).grid(row=6, column=0, pady=8, sticky="w")

        ttk.Label(frame, textvariable=self.status_var).grid(row=7, column=0, columnspan=2, sticky="w")
        ttk.Label(frame, textvariable=self.result_var).grid(row=8, column=0, columnspan=2, sticky="w")

        frame.columnconfigure(1, weight=1)

    def apply_rules(self) -> None:
        fixed_lot = self._to_float_or_none(self.fixed_lot_entry.get())
        ratio = self._to_float_or_default(self.ratio_entry.get(), 1.0)
        magics = self._parse_magics(self.magic_entry.get())

        self.service.engine.rule = CopierRule(
            reverse=self.reverse_var.get(),
            fixed_lot=fixed_lot,
            lot_ratio=ratio,
            allowed_magics=magics,
        )
        self.result_var.set("最近结果：规则已更新")

    def start_service(self) -> None:
        self.service.start()
        self.status_var.set("状态：运行中")

    def stop_service(self) -> None:
        self.service.stop()
        self.status_var.set("状态：已停止")

    def simulate_event(self) -> None:
        event = TradeEvent(
            ticket=random.randint(10000, 99999),
            symbol="EURUSD",
            side=random.choice([OrderSide.BUY, OrderSide.SELL]),
            volume=0.1,
            magic=random.choice([100, 200, 300]),
            floating_profit=random.choice([-15.0, 5.0, 20.0]),
            action=ActionType.OPEN,
        )
        result = self.service.process_event(event)
        if result.copied_order:
            self.result_var.set(
                f"最近结果：已跟单 src={event.ticket} -> dst={result.target_ticket} {result.copied_order.side.value} {result.copied_order.volume}"
            )
        else:
            self.result_var.set(f"最近结果：信号被过滤 src={event.ticket}")

    @staticmethod
    def _to_float_or_none(raw: str) -> float | None:
        raw = raw.strip()
        if not raw:
            return None
        return float(raw)

    @staticmethod
    def _to_float_or_default(raw: str, default: float) -> float:
        raw = raw.strip()
        if not raw:
            return default
        return float(raw)

    @staticmethod
    def _parse_magics(raw: str) -> set[int] | None:
        raw = raw.strip()
        if not raw:
            return None
        values = {int(item.strip()) for item in raw.split(",") if item.strip()}
        return values or None


def main() -> None:
    app = CopierApp()
    app.mainloop()


if __name__ == "__main__":
    main()
