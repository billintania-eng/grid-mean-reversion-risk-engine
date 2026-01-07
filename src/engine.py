from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Fill:
    price: float
    lots: float


@dataclass
class BookSnapshot:
    total_lots: float
    wap: Optional[float]
    unrealised_pnl: float
    worst_case_unrealised_pnl: float


class PositionBook:
    """
    Aggregates multiple fills into a single effective exposure.
    Provides WAP, unrealised PnL, and worst-case intrabar unrealised PnL.
    """

    def __init__(self, contract_size: float = 100.0):
        self.contract_size = float(contract_size)
        self.fills: List[Fill] = []

    def add_fill(self, price: float, lots: float) -> None:
        if lots <= 0:
            return
        self.fills.append(Fill(float(price), float(lots)))

    def clear(self) -> None:
        self.fills.clear()

    @property
    def total_lots(self) -> float:
        return sum(f.lots for f in self.fills)

    @property
    def wap(self) -> Optional[float]:
        tl = self.total_lots
        if tl <= 0:
            return None
        return sum(f.price * f.lots for f in self.fills) / tl

    def unrealised_pnl(self, mark_price: float) -> float:
        """PnL if we mark using a single price (e.g., Close)."""
        if self.total_lots <= 0 or self.wap is None:
            return 0.0
        return (float(mark_price) - self.wap) * self.total_lots * self.contract_size

    def worst_case_unrealised_pnl(self, worst_price: float) -> float:
        """
        Worst-case intrabar PnL for long-only book.
        For BUY exposure, worst price is typically bar LOW.
        """
        if self.total_lots <= 0 or self.wap is None:
            return 0.0
        return (float(worst_price) - self.wap) * self.total_lots * self.contract_size

    def snapshot(self, close_price: float, worst_price: float) -> BookSnapshot:
        return BookSnapshot(
            total_lots=self.total_lots,
            wap=self.wap,
            unrealised_pnl=self.unrealised_pnl(close_price),
            worst_case_unrealised_pnl=self.worst_case_unrealised_pnl(worst_price),
        )
