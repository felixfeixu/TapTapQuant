# 第 0 天 · 概念、环境、读库（2 小时）

目标：能讲清量化在干什么；电脑上有一套可复用的 Python 环境；知道开源库分几层、该怎么读。不写策略、不拉行情。

---

### A. 基本概念（35 分钟）

先建立地图，再碰代码。看不懂的词记下，不要开新标签页连环搜。

**量化是什么**

- [ ] 量化交易 = 把买卖决策写成可重复的规则（或模型），用数据检验，再决定是否自动执行
- [ ] 它不是「预测明天涨跌」，也不是「把机器学习接到行情上就赚钱」
- [ ] 程序员优势：数据管道、版本管理、回测可复现、把规则写成代码。金融直觉后面几天补

**一条流水线（记住这 6 格）**

```
数据 → 特征/信号 → 仓位 → 执行 → 盈亏 → 风控
```

- [ ] 业余路径：**研究 → 回测 → 风控 → 模拟盘 → 小资金实盘**。跳步是最常见的失败原因
- [ ] 今天只准备流水线左边的「环境」；数据从 `day1.md` 开始

**今天必须认识的词（各用一句话写进笔记）**

| 词 | 一句话 |
| --- | --- |
| OHLCV | 开、高、低、收、成交量，日线研究的基本表 |
| 收益率 | 用涨跌比例而不是价格本身做比较 |
| 回测 | 用历史数据模拟「假如按规则交易」会发生什么 |
| 未来函数 | 用了当时不可能知道的信息，回测会假美 |
| 过拟合 | 规则只拟合了这段历史，换一段就失效 |
| 滑点/手续费 | 真实成交价和回测价的差；不计成本的曲线没有意义 |
| 样本内/外 | 调参用的数据和验收用的数据必须分开 |

**今天的范围（写死，后面几天不改）**

- [ ] 只选一个市场：A 股日线（`akshare`）或美股/ETF（`yfinance`）
- [ ] 三条约束：日线、现金、单标的。不碰杠杆、期货、期权、高频

### B. 程序员环境（40 分钟）

目标：以后每天打开就能写，而不是每天重装。

- [ ] Cursor / VS Code、Git（本地仓库即可）、Python（本机用启动器 `py`，不要敲 `python`——未进 PATH 时会跳微软商店）
- [ ] 先确认版本：`py --version`。3.11 / 3.12 最稳；3.14 的部分金融库可能还没轮子，装不上再改用 `py -3.12`

```powershell
cd E:\TapTapQuant
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install pandas numpy matplotlib jupyter akshare yfinance
```

创建环境用 `py`；激活后提示符会出现 `(.venv)`，这时的 `python` / `pip` 才是虚拟环境里的。若激活后 `python` 仍跳商店，改用 `.\.venv\Scripts\python.exe`。

- [ ] 确认 `python -c "import pandas, numpy, matplotlib"` 无报错（须在已激活的 `.venv` 里）
- [ ] 数据源二选一能 import 即可
- [ ] 建空目录：`data/` 缓存行情，`notebooks/` 实验，`src/` 可复用代码
- [ ] 今天不装回测框架、不装 TA-Lib、不装 vn.py
- [ ] 没有独显 / CUDA 完全够用。日频回测是 pandas 在 CPU 上算；核显只用来看图。不要装 PyTorch+CUDA、「GPU 加速回测」之类的东西

### C. 开源库怎么读（40 分钟）

不要通读文档。读量化库只找四件事：数据从哪进、策略怎么写、单怎么发、结果怎么度量。

**生态分层（10 分钟）**

```
行情获取    akshare / yfinance
清洗计算    pandas / numpy
回测        第 4 天再装框架
实盘        更后面，第 0 天完全不碰
```

- [ ] 能说出：现在处在「行情获取 + 清洗计算」层
- [ ] 能说出：事件驱动（每根 K 线走一次 `next()`）和向量化（整列算完）各一句

**精读一个小库（20 分钟）**

打开 [kernc/backtesting.py](https://github.com/kernc/backtesting.py) 的 README，找到 **Usage** 里的 `SmaCross` 示例（不要在标题或目录里找 `buy`/`sell`），超时就停：

- [ ] `init`：预处理，这里用 `self.I(...)` 登记两条均线
- [ ] `next`：每根 K 线调用一次；买卖不单独成段，而是写在 `next` 里面：`self.buy()` / `self.sell()`
- [ ] `Backtest(..., commission=.002)`：手续费从这里进
- [ ] `Strategy` / `Backtest` 的类签名扫一眼即可，不追实现
- [ ] 写下：数据最少哪些列、是逐 K 线还是整列、手续费在哪传入

`next` 里的「一根 K 线」= 你传入的数据表里的 **一行**。日线就每天调一次，5 分钟线就每 5 分钟调一次，月线就每月一次。库不规定周期，本课程前几天只用日线。

```
for 数据里的每一行:          # 日线 = 每个交易日；不是「5 日线 / 月线」除非你喂的就是那种
    把「现在」拨到这一行
    调用 strategy.next()     # 只在这里写买卖
    按规则撮合、记账
```

**扫一眼数据源（10 分钟）**

- A 股：[akfamily/akshare](https://github.com/akfamily/akshare) — 搜 `stock_zh_a_hist`
- 美股：[yfinance](https://github.com/ranaroussi/yfinance) — 看 `download` / `auto_adjust`

akshare **不需要 token**（那是 tushare 的事）。默认 `adjust=""` 是不复权；算均线、收益率用 **前复权** `adjust="qfq"`。只跑通下面这段，不要拉一年。

```python
import akshare as ak

# 平安银行 000001；period=daily 才是日线
df = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20260801",
    end_date="20260820",
    adjust="qfq",  # 前复权；"" 不复权，"hfq" 后复权
)
print(df.head())
print(df.columns)  # 中文列名：日期/开盘/收盘/最高/最低/成交量
```

- [ ] 记下：如何取日线、是否前复权、要不要 token
- [ ] 记下：接口不稳、频率限制、停牌空洞都当数据问题

### D. 收工（5 分钟）

1. 量化和「预测股价」差在哪？
2. 那条 6 格流水线是什么？
3. 环境怎么激活、包装了哪些？
4. 读一个回测库时该先找哪 4 个接口？

**不要做：** 写策略、拉一年行情、clone vn.py / Qlib、开实盘账户。
