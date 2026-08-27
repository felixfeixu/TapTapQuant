# -*- coding: utf-8 -*-
"""
Day2 任务 B：算均线、信号、仓位
- 信号用状态：收盘在 20 日均线上方为 1，否则为 0（不做交叉检测）
- 仓位先等于信号（偷看当天收盘；shift(1) 留给 day3）
- 画出：收盘价 + 均线，以及仓位 0/1 时间轴
"""

import sys
from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from day1_b import DATA_DIR, SYMBOL, load_daily
from day2_a import MA_WINDOW, ma_close

OUT_PATH: Final[Path] = DATA_DIR / f"{SYMBOL}_ma20_position.png"


def state_signal(close: pd.Series, ma: pd.Series) -> pd.Series:
    """每天的「想持有多少」，不是买卖脉冲。

    1 = 收盘在均线上方（想满仓），0 = 在下方（想空仓）。
    均线预热期为 NaN，当成 0。连续多天为 1 表示一直拿着，不是每天都新买一次。
    """
    above: pd.Series = close > ma
    signal: pd.Series = above.astype("float64").fillna(0.0)
    return signal


def position_equals_signal(signal: pd.Series) -> pd.Series:
    """仓位和信号是同一列 0/1：想满仓的日子就当成已经满仓。

    这里的信号已经是「持有状态」，所以仓位 = 信号是字面相等。
    若信号改成上穿/下穿那种只在穿越日为 True 的脉冲，就不能直接相等，
    而要：碰到买入脉冲 → 之后一直满仓，碰到卖出脉冲 → 之后一直空仓。
    对本规则，两种写法结果几乎一样（站上均线期间状态一直是 1）。
    真正可执行的仓位仍见 day3：signal.shift(1)。
    """
    position: pd.Series = signal.copy()
    return position


def plot_close_ma_position(
    close: pd.Series,
    ma: pd.Series,
    position: pd.Series,
    out_path: Path,
    symbol: str,
    window: int,
) -> Path:
    """上图收盘价与均线，下图仓位 0/1。"""
    fig: Figure
    ax_price: Axes
    ax_pos: Axes
    fig, (ax_price, ax_pos) = plt.subplots(
        nrows=2,
        ncols=1,
        sharex=True,
        figsize=(10, 7),
        layout="constrained",
        height_ratios=(2, 1),
    )

    ax_price.plot(close.index, close.to_numpy(), color="C0", linewidth=1.0, label="close")
    ax_price.plot(ma.index, ma.to_numpy(), color="C1", linewidth=1.0, label=f"MA{window}")
    ax_price.set_ylabel("Price")
    ax_price.set_title(f"{symbol} close vs MA{window}")
    ax_price.legend(loc="upper left", fontsize=8)
    ax_price.grid(True, alpha=0.3)

    ax_pos.fill_between(
        position.index,
        0.0,
        position.to_numpy(),
        step="post",
        color="C2",
        alpha=0.45,
        label="position = signal (lookahead)",
    )
    ax_pos.set_ylabel("Position")
    ax_pos.set_xlabel("Date")
    ax_pos.set_ylim(-0.05, 1.15)
    ax_pos.set_yticks([0.0, 1.0])
    ax_pos.set_yticklabels(["flat 0", "long 1"])
    ax_pos.legend(loc="upper left", fontsize=8)
    ax_pos.grid(True, alpha=0.3)

    out_path.parent.mkdir(exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    df: pd.DataFrame = load_daily(DATA_DIR, SYMBOL)
    close: pd.Series = df["close"]
    ma20: pd.Series = ma_close(close, MA_WINDOW)
    signal: pd.Series = state_signal(close, ma20)
    position: pd.Series = position_equals_signal(signal)

    n_long: int = int((position == 1.0).sum())
    n_flat: int = int((position == 0.0).sum())
    n_change: int = int(position.diff().fillna(0.0).ne(0.0).sum())

    saved: Path = plot_close_ma_position(
        close=close,
        ma=ma20,
        position=position,
        out_path=OUT_PATH,
        symbol=SYMBOL,
        window=MA_WINDOW,
    )

    print(f"标的: {SYMBOL}  区间: {close.index[0].date()} ~ {close.index[-1].date()}")
    print(f"信号定义: close > MA{MA_WINDOW} → 1，否则 0（状态，不是上穿/下穿）")
    print(f"仓位 = 信号（未 shift；day3 再改）")
    print(f"满仓天数: {n_long}  空仓天数: {n_flat}  仓位变化次数: {n_change}")
    print(f"已保存: {saved}")


if __name__ == "__main__":
    main()
