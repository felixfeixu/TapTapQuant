# -*- coding: utf-8 -*-
"""
Day2 任务 A：规定规则（只写这一条，不要改来改去）
- 收盘价上穿 20 日均线 → 满仓（仓位 1）
- 收盘价下穿 20 日均线 → 空仓（仓位 0）
- 单标的、不允许做空、不加杠杆
- 用中文写出进出场，避免「金叉」这种含糊词
- 只算均线和穿越次数；信号/仓位图留给 day2_b.py
"""

import sys
from typing import Final

import pandas as pd

from day1_b import DATA_DIR, SYMBOL, load_daily

MA_WINDOW: Final[int] = 20
LONG_POS: Final[float] = 1.0
FLAT_POS: Final[float] = 0.0

# 进出场条件（中文，可执行；不用「金叉/死叉」）
ENTRY_CN: Final[str] = (
    f"进场：昨天收盘价 <= {MA_WINDOW} 日均线，"
    f"并且今天收盘价 > {MA_WINDOW} 日均线 → 仓位置为 {LONG_POS}（满仓）。"
)
EXIT_CN: Final[str] = (
    f"出场：昨天收盘价 >= {MA_WINDOW} 日均线，"
    f"并且今天收盘价 < {MA_WINDOW} 日均线 → 仓位置为 {FLAT_POS}（空仓）。"
)
CONSTRAINT_CN: Final[str] = (
    "约束：只做这一只标的；空仓就是现金，不允许做空；不加杠杆。"
)


def ma_close(close: pd.Series, window: int) -> pd.Series:
    """收盘价的滚动均值。前 window-1 根为 NaN（预热）。"""
    ma: pd.Series = close.rolling(window=window, min_periods=window).mean()
    return ma


def cross_up(close: pd.Series, ma: pd.Series) -> pd.Series:
    """上穿：昨收在均线下方或刚好碰上，今收站上均线。"""
    prev_close: pd.Series = close.shift(1)
    prev_ma: pd.Series = ma.shift(1)
    hit: pd.Series = (prev_close <= prev_ma) & (close > ma)
    return hit.fillna(False)


def cross_down(close: pd.Series, ma: pd.Series) -> pd.Series:
    """下穿：昨收在均线上方或刚好碰上，今收跌破均线。"""
    prev_close: pd.Series = close.shift(1)
    prev_ma: pd.Series = ma.shift(1)
    hit: pd.Series = (prev_close >= prev_ma) & (close < ma)
    return hit.fillna(False)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    df: pd.DataFrame = load_daily(DATA_DIR, SYMBOL)
    close: pd.Series = df["close"]
    ma20: pd.Series = ma_close(close, MA_WINDOW)
    warmup_bars: int = int(ma20.isna().sum())
    n_bars: int = len(close)

    print("=" * 50)
    print("规则（写死，后面几天不改）")
    print(ENTRY_CN)
    print(EXIT_CN)
    print(CONSTRAINT_CN)
    print("和买入持有的差别：买入持有整段只买一次、卖一次；"
          "本规则在样本里可以反复进场、出场。")
    print("=" * 50)

    print(f"标的: {SYMBOL}  区间: {close.index[0].date()} ~ {close.index[-1].date()}")
    print(f"K 线根数: {n_bars}  均线窗口: {MA_WINDOW}")
    print(f"预热（均线仍是 NaN）: {warmup_bars} 根 → 这些天不会满仓")
    if n_bars < MA_WINDOW:
        print("数据短于均线窗口，这条规则几乎没法交易。")
        return

    up: pd.Series = cross_up(close, ma20)
    down: pd.Series = cross_down(close, ma20)
    n_entry: int = int(up.sum())
    n_exit: int = int(down.sum())

    print(f"上穿（进场）次数: {n_entry}")
    print(f"下穿（出场）次数: {n_exit}")
    print("前 5 次进场日:", [d.date() for d in close.index[up][:5]])
    print("前 5 次出场日:", [d.date() for d in close.index[down][:5]])


if __name__ == "__main__":
    main()
