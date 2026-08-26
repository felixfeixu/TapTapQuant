# -*- coding: utf-8 -*-
"""
Day1 任务 A：拉日线并落盘
- 用 akshare 拉贵州茅台(600519) 最近 2 年日线（前复权）
- 列名统一为 open/high/low/close/volume，索引为交易日
- 打印 head/tail/describe 和缺失值数量，检查停牌/丢行空洞
- 存到 data/ 目录（parquet + csv），后面几天直接读本地文件
"""

import os
from pathlib import Path
from typing import Final

# 国内数据源(东财)不需要走代理，系统代理反而会连不上
for _k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
    os.environ.pop(_k, None)
os.environ["NO_PROXY"] = "*"

import akshare as ak
import pandas as pd

SYMBOL: Final[str] = "600519"          # 贵州茅台；想换标的改这里
NAME: Final[str] = "贵州茅台"
YEARS: Final[int] = 2                  # 取最近 N 年
DATA_DIR: Final[Path] = Path(__file__).parent / "data"


def _fetch_from_eastmoney(symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """数据源 1：东方财富（首选）。"""
    raw = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start.strftime("%Y%m%d"),
        end_date=end.strftime("%Y%m%d"),
        adjust="qfq",
    )
    if raw is None or raw.empty:
        raise RuntimeError("东财返回空数据")
    df: pd.DataFrame = raw.rename(
        columns={
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


def _fetch_from_sina(symbol: str) -> pd.DataFrame:
    """数据源 2：新浪（备选，东财连不上时用）。返回全历史，需外部按区间裁剪。"""
    raw: DataFrame = ak.stock_zh_a_daily(
        symbol=f"sh{symbol}",
        start_date=None,
        end_date=None,
        adjust="qfq",
    )
    if raw is None or raw.empty:
        raise RuntimeError("新浪返回空数据")
    df = raw.rename(columns={"date": "date"})[["date", "open", "high", "low", "close", "volume"]]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


def fetch_daily(symbol: str, years: int = 2) -> pd.DataFrame:
    """拉取 A 股日线（前复权），东财失败自动切新浪。"""
    end: Final[pd.Timestamp] = pd.Timestamp.today()
    start: Final[pd.Timestamp] = end - pd.DateOffset(years=years)

    last_err: Exception | None = None
    for name, fetcher in (
        ("eastmoney", lambda: _fetch_from_eastmoney(symbol, start, end)),
        ("sina", lambda: _fetch_from_sina(symbol)),
    ):
        try:
            print(f"尝试数据源: {name} ...")
            df = fetcher()
            # 统一裁剪到最近 N 年
            df = df.loc[start:end]
            keep: list[str] = ["open", "high", "low", "close", "volume"]
            return df[keep].astype(float)
        except Exception as e:
            print(f"数据源 {name} 失败: {e}")
            last_err = e

    raise RuntimeError(f"所有数据源都失败，最后错误: {last_err}")


def check_gaps(df: pd.DataFrame) -> None:
    """打印基础信息，粗查停牌/节假日/丢行造成的空洞。"""
    print("=" * 60)
    print("head:")
    print(df.head())
    print("\ntail:")
    print(df.tail())
    print("\ndescribe:")
    print(df.describe())

    print("\n缺失值数量:")
    print(df.isna().sum())

    # 日历日跨度 vs 实际交易天数：A股一年约 243 个交易日
    span_days = (df.index[-1] - df.index[0]).days
    n_bars = len(df)
    print(f"\n区间: {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"自然日 {span_days} 天，实际 {n_bars} 根 K 线 "
          f"(约 {span_days / n_bars:.2f} 自然日/K线，正常约 1.46)")

    # 相邻两根 K 线间隔超过 10 个自然日视为可疑长空洞（春节+国庆最多也就 9 天左右）
    gaps = df.index.to_series().diff().dt.days
    long_gaps = gaps[gaps > 10]
    if long_gaps.empty:
        print("未发现超过 10 天的可疑空洞")
    else:
        print("发现可疑长空洞（可能是接口丢行）:")
        print(long_gaps)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df: pd.DataFrame = fetch_daily(SYMBOL, YEARS)
    check_gaps(df)

    csv_path: Path = DATA_DIR / f"{SYMBOL}_daily_qfq.csv"
    pq_path: Path = DATA_DIR / f"{SYMBOL}_daily_qfq.parquet"
    df.to_csv(csv_path, encoding="utf-8-sig")
    try:
        df.to_parquet(pq_path)
    except Exception as e:  # 没装 pyarrow 时退回只用 csv
        print(f"parquet 保存失败({e})，仅使用 csv")

    print(f"\n已保存: {csv_path}")


if __name__ == "__main__":
    main()
