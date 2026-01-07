from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class StrategyConfig:
    grid_size: float = 25.0
    base_lots: float = 10.0
    # re-arm: ต้องลงทะลุ level - grid_size ก่อน ถึงจะ “ตั้งรอใหม่” ได้
    rearm_buffer_levels: int = 1


@dataclass
class Signal:
    action: str                 # "BUY" | "NONE"
    entry_level: Optional[float]
    lots: float
    depth_levels: int


class VShapeRearmStrategy:
    """
    V-shape logic:
    - price falls below a grid level -> "armed"
    - if falls too deep beyond level - buffer -> disarm
    - on bounce back to level -> BUY (size depends on depth)
    - re-arm allowed even if there are open positions (as you wanted)
    """

    def __init__(self, cfg: StrategyConfig):
        self.cfg = cfg
        self.armed_level: Optional[float] = None
        self.lowest_price_while_armed: Optional[float] = None

    def reset(self) -> None:
        self.armed_level = None
        self.lowest_price_while_armed = None

    def _nearest_grid(self, price: float) -> float:
        g = self.cfg.grid_size
        return round(price / g) * g

    def on_bar(self, open_: float, high: float, low: float, close: float) -> Signal:
        g = self.cfg.grid_size
        buffer = self.cfg.rearm_buffer_levels * g

        # เลือก “level อ้างอิง” จากราคา open/close ก็ได้ — โดยทั่วไปใช้ close
        level = self._nearest_grid(close)

        # (1) ถ้ายังไม่ armed และราคาลงมาแตะ/ต่ำกว่า level -> armed
        if self.armed_level is None and low <= level:
            self.armed_level = level
            self.lowest_price_while_armed = low
            return Signal("NONE", None, 0.0, 0)

        # (2) ถ้า armed อยู่ อัปเดต lowest
        if self.armed_level is not None:
            self.lowest_price_while_armed = min(self.lowest_price_while_armed, low)  # type: ignore

            # (2a) ถ้ารูดลึกเกิน buffer -> ยกเลิกการรอ (disarm)
            if low <= (self.armed_level - buffer):
                self.reset()
                return Signal("NONE", None, 0.0, 0)

            # (2b) ถ้าดีดกลับขึ้นมาถึง armed_level -> BUY
            if high >= self.armed_level:
                depth_levels = max(1, int(math.floor((self.armed_level - self.lowest_price_while_armed) / g)) + 1)  # type: ignore
                lots = self.cfg.base_lots * depth_levels
                entry = self.armed_level
                self.reset()
                return Signal("BUY", entry, lots, depth_levels)

        return Signal("NONE", None, 0.0, 0)
