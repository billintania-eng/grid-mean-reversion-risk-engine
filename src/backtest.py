from __future__ import annotations
import os
import pandas as pd
import matplotlib.pyplot as plt

from engine import PositionBook
from strategy import StrategyConfig, VShapeRearmStrategy


def run_backtest(df: pd.DataFrame,
                 initial_cash: float = 1_000_000.0,
                 contract_size: float = 100.0,
                 grid_size: float = 25.0,
                 base_lots: float = 10.0):
    # --- setup ---
    cash = float(initial_cash)
    book = PositionBook(contract_size=contract_size)

    strat = VShapeRearmStrategy(
        StrategyConfig(grid_size=grid_size, base_lots=base_lots, rearm_buffer_levels=1)
    )

    trade_log = []
    equity_rows = []

    peak_worst_equity = initial_cash
    max_dd_worst = 0.0

    # --- loop ---
    for i in range(len(df)):
        o = float(df["Open"].iloc[i])
        h = float(df["High"].iloc[i])
        l = float(df["Low"].iloc[i])
        c = float(df["Close"].iloc[i])
        ts = df.index[i]

        sig = strat.on_bar(o, h, l, c)

        # ENTRY
        if sig.action == "BUY" and sig.entry_level is not None:
            book.add_fill(price=sig.entry_level, lots=sig.lots)
            trade_log.append({
                "Date": ts,
                "Type": "BUY",
                "EntryLevel": sig.entry_level,
                "Lots": sig.lots,
                "DepthLevels": sig.depth_levels,
                "WAP_After": book.wap,
                "TotalLots_After": book.total_lots,
            })

        # EXIT (fixed TP = WAP + grid_size) แบบง่าย
        # ถ้าคุณมี logic TP เฉพาะ “entry_level + grid_size” ให้เปลี่ยนตรงนี้
        if book.total_lots > 0 and book.wap is not None:
            tp = book.wap + grid_size
            if h >= tp:
                # ปิดทั้งหมดที่ tp
                realised = (tp - book.wap) * book.total_lots * contract_size
                cash += realised
                trade_log.append({
                    "Date": ts,
                    "Type": "SELL",
                    "ExitPrice": tp,
                    "LotsClosed": book.total_lots,
                    "RealisedPnL": realised,
                })
                book.clear()

        snap = book.snapshot(close_price=c, worst_price=l)
        equity_close = cash + snap.unrealised_pnl
        equity_worst = cash + snap.worst_case_unrealised_pnl

        peak_worst_equity = max(peak_worst_equity, equity_worst)
        dd_worst = (peak_worst_equity - equity_worst) / peak_worst_equity * 100 if peak_worst_equity > 0 else 0.0
        max_dd_worst = max(max_dd_worst, dd_worst)

        equity_rows.append({
            "Date": ts,
            "Cash": cash,
            "TotalLots": snap.total_lots,
            "WAP": snap.wap,
            "EquityClose": equity_close,
            "EquityWorst": equity_worst,
            "DDWorstPct": dd_worst,
        })

    trades_df = pd.DataFrame(trade_log)
    equity_df = pd.DataFrame(equity_rows)

    result = {
        "FinalEquityWorst": float(equity_df["EquityWorst"].iloc[-1]),
        "PeakEquityWorst": float(equity_df["EquityWorst"].max()),
        "MaxDDWorstPct": float(max_dd_worst),
        "Trades": trades_df,
        "Equity": equity_df,
    }
    return result


def export_outputs(result, out_dir="outputs"):
    os.makedirs(out_dir, exist_ok=True)

    trades_df = result["Trades"]
    equity_df = result["Equity"]

    # Excel
    xlsx_path = os.path.join(out_dir, "backtest_outputs.xlsx")
    with pd.ExcelWriter(xlsx_path) as w:
        trades_df.to_excel(w, sheet_name="TradeLog", index=False)
        equity_df.to_excel(w, sheet_name="EquityCurve", index=False)

    # PNG
    plt.figure(figsize=(12,5))
    plt.plot(equity_df["Date"], equity_df["EquityWorst"])
    plt.title("Equity Curve (Worst-case, V-shape + Re-arm)")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.tight_layout()
    png_path = os.path.join(out_dir, "equity_worst_case.png")
    plt.savefig(png_path, dpi=160)
    plt.close()

    return xlsx_path, png_path


if __name__ == "__main__":
    # TODO: replace this with your actual data loader
    # df must have columns: Open, High, Low, Close and datetime index

    raise SystemExit("Please wire your data loader here (df with OHLC).")
