# -*- coding: utf-8 -*-
"""
Day2 任务 C：策略收益 vs 买入持有
- 策略日收益 = 当日仓位 × 标的日收益（明知偷看收盘，先跑通）
- 叠两条累计收益：策略 vs 买入持有
- 仓位 0↔1 各扣成交额 0.1%（佣金+印花税粗影子）
- 打印交易次数、扣成本后总收益、最大回撤
"""

import sys
from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from day1_b import DATA_DIR, SYMBOL, load_daily
from day1_c import buy_and_hold_nav
from day2_a import MA_WINDOW, ma_close
from day2_b import position_equals_signal, state_signal

COST_RATE: Final[float] = 0.001  # 单边 0.1%
OUT_PATH: Final[Path] = DATA_DIR / f"{SYMBOL}_ma20_vs_buyhold.png"


def asset_daily_return(close: pd.Series) -> pd.Series:
    """标的日收益。第一根没有昨收，当成 0。"""
    ret: pd.Series = close.pct_change().fillna(0.0)
    return ret


def turnover(position: pd.Series) -> pd.Series:
    """|Δ仓位|。从空仓起步，0→1 和 1→0 都记一次成交。"""
    prev: pd.Series = position.shift(1).fillna(0.0)
    traded: pd.Series = (position - prev).abs()
    return traded


def strategy_return(
    position: pd.Series,
    asset_ret: pd.Series,
    cost_rate: float,
) -> tuple[pd.Series, pd.Series]:
    """返回（未扣成本日收益, 扣成本日收益）。成本只在仓位变化日扣除。"""
    gross: pd.Series = position * asset_ret
    cost: pd.Series = turnover(position) * cost_rate
    net: pd.Series = gross - cost
    return gross, net


def nav_from_return(daily_ret: pd.Series) -> pd.Series:
    """日收益累乘净值，期初 = 1。"""
    nav: pd.Series = (1.0 + daily_ret).cumprod()
    return nav


def max_drawdown(nav: pd.Series) -> float:
    peak: pd.Series = nav.cummax()
    drawdown: pd.Series = nav / peak - 1.0
    return float(drawdown.min())


def plot_cum_return(
    bh_cum: pd.Series,
    strat_gross_cum: pd.Series,
    strat_net_cum: pd.Series,
    out_path: Path,
    symbol: str,
) -> Path:
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    ax.plot(bh_cum.index, bh_cum.to_numpy(), color="C0", linewidth=1.2, label="buy & hold")
    ax.plot(
        strat_gross_cum.index,
        strat_gross_cum.to_numpy(),
        color="C1",
        linewidth=1.0,
        linestyle="--",
        label="MA20 gross (lookahead)",
    )
    ax.plot(
        strat_net_cum.index,
        strat_net_cum.to_numpy(),
        color="C3",
        linewidth=1.2,
        label=f"MA20 net (cost {COST_RATE:.1%} per trade)",
    )
    ax.set_title(f"{symbol} cumulative return: MA20 vs buy & hold")
    ax.set_ylabel("Cumulative return")
    ax.set_xlabel("Date")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

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
    # 信号：该日收盘在均线上方 → 1（想满仓），否则 0（想空仓）
    signal: pd.Series = state_signal(close, ma20)
    # 仓位：账户当天实际持股比例，0=现金，1=全仓该股。
    # 第 2 天故意让仓位 = 信号（用当天收盘既判断又持有；day3 再 shift(1)）
    position: pd.Series = position_equals_signal(signal)
    asset_ret: pd.Series = asset_daily_return(close)
    traded: pd.Series = turnover(position)

    gross_ret: pd.Series
    net_ret: pd.Series
    gross_ret, net_ret = strategy_return(position, asset_ret, COST_RATE)

    bh_nav: pd.Series = buy_and_hold_nav(close)
    gross_nav: pd.Series = nav_from_return(gross_ret)
    net_nav: pd.Series = nav_from_return(net_ret)

    n_trades: int = int((traded > 0).sum())
    n_round_trips: float = n_trades / 2.0
    bh_total: float = float(bh_nav.iloc[-1] - 1.0)
    gross_total: float = float(gross_nav.iloc[-1] - 1.0)
    net_total: float = float(net_nav.iloc[-1] - 1.0)
    bh_mdd: float = max_drawdown(bh_nav)
    gross_mdd: float = max_drawdown(gross_nav)
    net_mdd: float = max_drawdown(net_nav)

    saved: Path = plot_cum_return(
        bh_cum=bh_nav - 1.0,
        strat_gross_cum=gross_nav - 1.0,
        strat_net_cum=net_nav - 1.0,
        out_path=OUT_PATH,
        symbol=SYMBOL,
    )

    print(f"标的: {SYMBOL}  区间: {close.index[0].date()} ~ {close.index[-1].date()}")
    print(f"仓位 = 信号（当日仓位 × 当日收益，未 shift）")
    print(f"交易次数（0↔1）: {n_trades}  约 {n_round_trips:.0f} 个来回")
    print(f"单边成本: {COST_RATE:.2%}")
    print("=" * 52)
    print(f"{'':16} {'总收益':>12} {'最大回撤':>12}")
    print(f"{'买入持有':16} {bh_total:12.2%} {bh_mdd:12.2%}")
    print(f"{'策略未扣成本':16} {gross_total:12.2%} {gross_mdd:12.2%}")
    print(f"{'策略扣成本后':16} {net_total:12.2%} {net_mdd:12.2%}")
    print("=" * 52)
    print("用当天收盘价成交是错的，day3 用 shift(1) 改。")
    print(f"已保存: {saved}")


if __name__ == "__main__":
    main()
