# -*- coding: utf-8 -*-
"""
Day1 任务 C：画两张图
- 读取 day1_a.py 落盘的日线（不重复打接口）
- 上图：收盘价；下图：买入持有累计收益
- 两图都标出最大回撤区间（峰值 → 回撤低点）
- 图片存到 data/，后面几天叠策略曲线时用
"""

import sys
from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from day1_b import DATA_DIR, SYMBOL, load_daily

OUT_PATH: Final[Path] = DATA_DIR / f"{SYMBOL}_buy_hold.png"


def buy_and_hold_nav(close: pd.Series) -> pd.Series:
    """日收益累乘得到买入持有净值，期初 = 1。"""
    ret: pd.Series = close.pct_change()
    nav: pd.Series = (1 + ret.fillna(0)).cumprod()
    return nav


def max_drawdown_window(nav: pd.Series) -> tuple[pd.Timestamp, pd.Timestamp, float]:
    """最大回撤区间：回撤开始的峰值日、最低点日、回撤幅度（负数）。"""
    peak: pd.Series = nav.cummax()
    drawdown: pd.Series = nav / peak - 1
    trough_date: pd.Timestamp = pd.Timestamp(drawdown.idxmin())
    before_trough: pd.Series = nav.loc[:trough_date]
    peak_date: pd.Timestamp = pd.Timestamp(before_trough.idxmax())
    max_drawdown: float = float(drawdown.min())
    return peak_date, trough_date, max_drawdown


def _shade_mdd(
    ax: Axes,
    peak_date: pd.Timestamp,
    trough_date: pd.Timestamp,
    label: str,
) -> None:
    ax.axvspan(peak_date, trough_date, color="0.75", alpha=0.5, label=label)
    ax.axvline(peak_date, color="0.4", linestyle="--", linewidth=0.8)
    ax.axvline(trough_date, color="0.4", linestyle="--", linewidth=0.8)


def plot_close_and_return(
    close: pd.Series,
    nav: pd.Series,
    peak_date: pd.Timestamp,
    trough_date: pd.Timestamp,
    max_drawdown: float,
    out_path: Path,
    symbol: str,
) -> Path:
    """画收盘价 + 累计收益，阴影标出最大回撤区间，保存 png。"""
    cum_return: pd.Series = nav - 1
    mdd_label: str = (
        f"MDD {max_drawdown:.1%}  {peak_date.date()} ~ {trough_date.date()}"
    )

    fig: Figure
    ax_close: Axes
    ax_ret: Axes
    fig, (ax_close, ax_ret) = plt.subplots(
        nrows=2,
        ncols=1,
        sharex=True,
        figsize=(10, 7),
        layout="constrained",
    )

    ax_close.plot(close.index, close.to_numpy(), color="C0", linewidth=1.0)
    _shade_mdd(ax_close, peak_date, trough_date, mdd_label)
    ax_close.set_ylabel("Close")
    ax_close.set_title(f"{symbol} close")
    ax_close.legend(loc="upper left", fontsize=8)
    ax_close.grid(True, alpha=0.3)

    ax_ret.plot(cum_return.index, cum_return.to_numpy(), color="C1", linewidth=1.0)
    _shade_mdd(ax_ret, peak_date, trough_date, mdd_label)
    ax_ret.set_ylabel("Cumulative return")
    ax_ret.set_title(f"{symbol} buy-and-hold cumulative return")
    ax_ret.set_xlabel("Date")
    ax_ret.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax_ret.legend(loc="upper left", fontsize=8)
    ax_ret.grid(True, alpha=0.3)

    out_path.parent.mkdir(exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    df: pd.DataFrame = load_daily(DATA_DIR, SYMBOL)
    close: pd.Series = df["close"]
    nav: pd.Series = buy_and_hold_nav(close)
    peak_date: pd.Timestamp
    trough_date: pd.Timestamp
    max_drawdown: float
    peak_date, trough_date, max_drawdown = max_drawdown_window(nav)

    saved: Path = plot_close_and_return(
        close=close,
        nav=nav,
        peak_date=peak_date,
        trough_date=trough_date,
        max_drawdown=max_drawdown,
        out_path=OUT_PATH,
        symbol=SYMBOL,
    )

    print(f"区间: {close.index[0].date()} ~ {close.index[-1].date()}")
    print(f"最大回撤: {max_drawdown:.2%}  {peak_date.date()} → {trough_date.date()}")
    print(f"已保存: {saved}")


if __name__ == "__main__":
    main()
