# -*- coding: utf-8 -*-
"""
Day1 任务 B：收益率，不是价格
- 读取 day1_a.py 落盘到 data/ 的日线（不重复打接口）
- 日收益 ret = close.pct_change()
- 累计净值 nav = (1 + ret).cumprod()，即买入持有基线
- 最大回撤 = 净值相对历史峰值的最大跌幅
- 打印区间总收益、最大回撤、年化波动率三个数
"""

from pathlib import Path
from typing import Final

import pandas as pd

SYMBOL: Final[str] = "600519"                       # 与 day1_a.py 保持一致
DATA_DIR: Final[Path] = Path(__file__).parent / "data"
TRADING_DAYS: Final[int] = 252                      # A股年化近似用的交易日数


def load_daily(data_dir: Path, symbol: str) -> pd.DataFrame:
    """读取本地日线。优先 parquet，退回 csv；都没有则提示先跑 day1_a.py。"""
    pq_path: Final[Path] = data_dir / f"{symbol}_daily_qfq.parquet"
    csv_path: Final[Path] = data_dir / f"{symbol}_daily_qfq.csv"

    if pq_path.exists():
        df = pd.read_parquet(pq_path)
    elif csv_path.exists():
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    else:
        raise FileNotFoundError(
            f"未找到 {pq_path} 或 {csv_path}，请先运行 day1_a.py 拉数据落盘"
        )

    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def compute_metrics(close: pd.Series) -> dict[str, float | pd.Timestamp]:
    """由收盘价算买入持有基线的核心指标：总收益、最大回撤、年化波动率。"""
    ret: Final[pd.Series] = close.pct_change()
    nav: Final[pd.Series] = (1 + ret.fillna(0)).cumprod()   # 期初净值 = 1

    total_return: Final[float] = float(nav.iloc[-1] - 1)

    peak: Final[pd.Series] = nav.cummax()
    drawdown: Final[pd.Series] = nav / peak - 1             # 始终 <= 0
    max_drawdown: Final[float] = float(drawdown.min())
    mdd_date: Final[pd.Timestamp] = drawdown.idxmin()

    daily_vol: Final[float] = float(ret.std())
    annual_vol: Final[float] = daily_vol * TRADING_DAYS ** 0.5   # 年化近似

    return {
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "max_drawdown_date": mdd_date,
        "daily_vol": daily_vol,
        "annual_vol": annual_vol,
    }


def main() -> None:
    df: Final[pd.DataFrame] = load_daily(DATA_DIR, SYMBOL)
    print(f"标的: {SYMBOL}  区间: {df.index[0].date()} ~ {df.index[-1].date()}  "
          f"共 {len(df)} 根K线")

    metrics: Final[dict[str, float | pd.Timestamp]] = compute_metrics(df["close"])

    print("=" * 40)
    print(f"区间总收益: {metrics['total_return']:.2%}")
    print(f"最大回撤:   {metrics['max_drawdown']:.2%}"
          f"（低点 {metrics['max_drawdown_date'].date()}）")
    print(f"年化波动率: {metrics['annual_vol']:.2%}")


if __name__ == "__main__":
    main()
