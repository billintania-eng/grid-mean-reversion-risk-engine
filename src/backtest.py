"""
Grid Mean Reversion Risk Engine (Research Prototype)

This module implements a grid-based mean reversion backtest
with a strong focus on portfolio-level risk, unrealised exposure,
and worst-case drawdown behaviour.

Research and educational use only.
"""

class GridMeanReversionEngine:
    def __init__(self, grid_size: float):
        self.grid_size = grid_size
        self.positions = []
        self.total_lots = 0.0
        self.wap_price = None

    def add_position(self, price: float, lots: float):
        self.positions.append((price, lots))
        self.total_lots += lots
        self.wap_price = sum(p * l for p, l in self.positions) / self.total_lots

    def unrealised_pnl(self, current_price: float) -> float:
        if self.total_lots == 0:
            return 0.0
        return (current_price - self.wap_price) * self.total_lots

    def worst_case_drawdown(self, worst_price: float) -> float:
        if self.total_lots == 0:
            return 0.0
        return (worst_price - self.wap_price) * self.total_lots

if __name__ == "__main__":
    engine = GridMeanReversionEngine(grid_size=25)

    engine.add_position(price=4450, lots=10)
    engine.add_position(price=4425, lots=20)

    print("WAP:", engine.wap_price)
    print("Unrealised PnL @ 4475:", engine.unrealised_pnl(4475))
    print("Worst-case DD @ 4350:", engine.worst_case_drawdown(4350))

