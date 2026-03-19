"""
app.py  ·  Crypto Paper Trading Bot — Streamlit Web App
════════════════════════════════════════════════════════
Deploy to Streamlit Cloud in one click.
No API keys needed — uses CoinGecko free tier.

Tabs
────
  📡 Live Market   — real-time BTC/ETH price + RSI chart
  📊 Signals       — buy/sell signal history with indicator table
  🧪 Backtest      — run + visualise historical strategy performance
  📂 CSV Upload    — drag-in your own backtest CSV for analysis
  ℹ️  Guide         — deployment & usage help
"""

# ── stdlib ────────────────────────────────────────────────────────────────────
import io
import time
import math
import random
from datetime import datetime, timezone, timedelta

# ── third-party ───────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG  (must be first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CryptoBot Pro",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS  — dark trading-terminal aesthetic
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Font ──────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root variables ───────────────────────────────────────────── */
:root {
    --green:  #00ff88;
    --red:    #ff4466;
    --yellow: #ffd700;
    --blue:   #4fc3f7;
    --bg:     #0a0e1a;
    --card:   #111827;
    --border: #1e293b;
    --muted:  #64748b;
    --text:   #e2e8f0;
}

/* ── Base ─────────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid var(--border);
}

/* ── Metric cards ─────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px !important;
    transition: border-color .2s;
}
[data-testid="metric-container"]:hover {
    border-color: var(--green);
}
[data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 1.6rem !important;
    color: var(--text) !important;
}
[data-testid="stMetricDelta"] { font-size: .85rem !important; }

/* ── Tabs ─────────────────────────────────────────────────────── */
.stTabs [role="tablist"] {
    background: var(--card);
    border-radius: 10px;
    padding: 4px;
    border: 1px solid var(--border);
    gap: 4px;
}
.stTabs [role="tab"] {
    border-radius: 8px !important;
    color: var(--muted) !important;
    font-weight: 500;
    transition: all .2s;
}
.stTabs [aria-selected="true"] {
    background: var(--green) !important;
    color: #000 !important;
    font-weight: 700;
}

/* ── Buttons ─────────────────────────────────────────────────── */
.stButton > button {
    background: transparent;
    border: 1px solid var(--green);
    color: var(--green);
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    border-radius: 8px;
    transition: all .2s;
}
.stButton > button:hover {
    background: var(--green);
    color: #000;
}
.stButton > button[kind="primary"] {
    background: var(--green);
    color: #000;
}

/* ── Selectbox / sliders ──────────────────────────────────────── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: var(--card) !important;
    border-color: var(--border) !important;
}

/* ── DataFrames ───────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Hero banner ──────────────────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, #0d1117 0%, #111827 50%, #0a1628 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(0,255,136,.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-family: 'Space Mono', monospace;
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--green);
    margin: 0 0 4px 0;
    letter-spacing: -1px;
}
.hero-sub {
    color: var(--muted);
    font-size: .95rem;
    margin: 0;
}

/* ── Signal badge ─────────────────────────────────────────────── */
.sig-buy  { background:#00ff8820; color:var(--green); border:1px solid #00ff8860;
            padding:3px 12px; border-radius:20px; font-weight:700; font-size:.82rem; }
.sig-sell { background:#ff446620; color:var(--red);   border:1px solid #ff446660;
            padding:3px 12px; border-radius:20px; font-weight:700; font-size:.82rem; }
.sig-hold { background:#ffd70020; color:var(--yellow);border:1px solid #ffd70060;
            padding:3px 12px; border-radius:20px; font-weight:700; font-size:.82rem; }

/* ── Info card ────────────────────────────────────────────────── */
.info-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    margin: 8px 0;
}
.info-card h4 { color: var(--green); margin: 0 0 8px 0; font-family: 'Space Mono', monospace; }

/* ── Price ticker ─────────────────────────────────────────────── */
.ticker {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -1px;
}
.ticker-up   { color: var(--green); }
.ticker-down { color: var(--red);   }

/* ── Step boxes (deploy guide) ───────────────────────────────── */
.step {
    background: var(--card);
    border-left: 3px solid var(--green);
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 10px 0;
}
.step-num {
    font-family: 'Space Mono', monospace;
    color: var(--green);
    font-weight: 700;
    font-size: .8rem;
    letter-spacing: 2px;
    text-transform: uppercase;
}

/* ── Scrollbar ────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
PAIRS = {
    "BTC/USDT": "bitcoin",
    "ETH/USDT": "ethereum",
    "SOL/USDT": "solana",
    "BNB/USDT": "binancecoin",
}
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
INITIAL_BALANCE = 10_000.0
FEE = 0.001


# ══════════════════════════════════════════════════════════════════════════════
#  DATA LAYER
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)
def fetch_price(coin_id: str) -> dict | None:
    """Fetch current price + 24h change from CoinGecko."""
    try:
        r = requests.get(
            f"{COINGECKO_BASE}/simple/price",
            params={"ids": coin_id, "vs_currencies": "usd",
                    "include_24hr_change": "true", "include_24hr_vol": "true"},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get(coin_id)
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ohlcv(coin_id: str, days: int = 90) -> pd.DataFrame:
    """
    Fetch OHLC candles from CoinGecko.
    Falls back to synthetic data on any network error.
    """
    try:
        r = requests.get(
            f"{COINGECKO_BASE}/coins/{coin_id}/ohlc",
            params={"vs_currency": "usd", "days": days},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            raise ValueError("empty")
        df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
        df.set_index("ts", inplace=True)
        df = df.astype(float)
        df["volume"] = (df["high"] - df["low"]) * 1_000
        return df
    except Exception:
        return _synthetic_ohlcv(days)


def _synthetic_ohlcv(days: int, seed: int = 42) -> pd.DataFrame:
    """Deterministic fake OHLCV — used when CoinGecko is unreachable."""
    rng  = np.random.default_rng(seed)
    n    = days * 24
    now  = datetime.now(timezone.utc)
    idx  = pd.date_range(end=now, periods=n, freq="h", tz="UTC")
    ret  = rng.normal(0.0002, 0.012, n)
    c    = 42_000 * np.cumprod(1 + ret)
    sp   = c * 0.005
    ns   = rng.uniform(-1, 1, n)
    df   = pd.DataFrame(index=idx)
    df.index.name = "ts"
    df["close"]  = c
    df["open"]   = c * (1 + rng.normal(0, 0.003, n))
    df["high"]   = c + np.abs(ns) * sp
    df["low"]    = c - np.abs(ns) * sp
    df["high"]   = df[["open","close","high"]].max(axis=1)
    df["low"]    = df[["open","close","low"]].min(axis=1)
    df["volume"] = rng.uniform(500, 5_000, n)
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  INDICATORS
# ══════════════════════════════════════════════════════════════════════════════

def calc_rsi(s: pd.Series, period: int = 14) -> pd.Series:
    d    = s.diff()
    g    = d.clip(lower=0)
    l    = -d.clip(upper=0)
    ag   = g.ewm(com=period - 1, min_periods=period).mean()
    al   = l.ewm(com=period - 1, min_periods=period).mean()
    rs   = ag / al.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def calc_sma(s: pd.Series, p: int) -> pd.Series:
    return s.rolling(p).mean()


def calc_ema(s: pd.Series, p: int) -> pd.Series:
    return s.ewm(span=p, adjust=False).mean()


def calc_macd(s: pd.Series):
    fast = calc_ema(s, 12)
    slow = calc_ema(s, 26)
    macd = fast - slow
    sig  = calc_ema(macd, 9)
    return macd, sig, macd - sig


def calc_bb(s: pd.Series, p: int = 20, std: float = 2.0):
    mid   = calc_sma(s, p)
    sigma = s.rolling(p).std()
    return mid + std * sigma, mid, mid - std * sigma


def enrich(df: pd.DataFrame, rsi_p: int, ma_s: int, ma_l: int) -> pd.DataFrame:
    df = df.copy()
    df["rsi"]      = calc_rsi(df["close"], rsi_p)
    df["sma_s"]    = calc_sma(df["close"], ma_s)
    df["sma_l"]    = calc_sma(df["close"], ma_l)
    df["ema12"]    = calc_ema(df["close"], 12)
    df["ema26"]    = calc_ema(df["close"], 26)
    df["macd"], df["macd_sig"], df["macd_hist"] = calc_macd(df["close"])
    df["bb_u"], df["bb_m"], df["bb_l"] = calc_bb(df["close"])
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  SIGNAL ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def generate_signals(df: pd.DataFrame, strategy: str,
                     rsi_os: int, rsi_ob: int) -> pd.DataFrame:
    """
    Annotate every row with signal, reason, and indicator snapshot.
    Returns a new DataFrame with added columns.
    """
    df = df.copy()
    signals, reasons = [], []

    for i in range(len(df)):
        sig, rsn = "HOLD", "—"
        row   = df.iloc[i]
        prev  = df.iloc[i - 1] if i > 0 else row

        if strategy == "MA Crossover":
            if pd.notna(row["sma_s"]) and pd.notna(row["sma_l"]):
                if prev["sma_s"] <= prev["sma_l"] and row["sma_s"] > row["sma_l"]:
                    sig, rsn = "BUY", f"Golden Cross SMA({df.index[i].strftime('%m-%d')})"
                elif prev["sma_s"] >= prev["sma_l"] and row["sma_s"] < row["sma_l"]:
                    sig, rsn = "SELL", f"Death Cross SMA({df.index[i].strftime('%m-%d')})"

        elif strategy == "RSI":
            if pd.notna(row["rsi"]):
                if prev["rsi"] >= rsi_os and row["rsi"] < rsi_os:
                    sig, rsn = "BUY", f"RSI oversold ({row['rsi']:.1f} < {rsi_os})"
                elif row["rsi"] > rsi_ob:
                    sig, rsn = "SELL", f"RSI overbought ({row['rsi']:.1f} > {rsi_ob})"

        elif strategy == "Combined":
            ma_buy = ma_sell = rsi_buy = rsi_sell = False
            if pd.notna(row["sma_s"]) and pd.notna(row["sma_l"]):
                ma_buy  = prev["sma_s"] <= prev["sma_l"] and row["sma_s"] > row["sma_l"]
                ma_sell = prev["sma_s"] >= prev["sma_l"] and row["sma_s"] < row["sma_l"]
            if pd.notna(row["rsi"]):
                rsi_buy  = prev["rsi"] >= rsi_os and row["rsi"] < rsi_os
                rsi_sell = row["rsi"] > rsi_ob
            if ma_buy  and rsi_buy:  sig, rsn = "BUY",  "Combined BUY (MA + RSI)"
            if ma_sell and rsi_sell: sig, rsn = "SELL", "Combined SELL (MA + RSI)"

        signals.append(sig)
        reasons.append(rsn)

    df["signal"] = signals
    df["reason"] = reasons
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  BACKTESTER
# ══════════════════════════════════════════════════════════════════════════════

def run_backtest(df: pd.DataFrame, pos_pct: float,
                 sl_pct: float, tp_pct: float) -> tuple[list, list, dict]:
    """
    Walk-forward simulation.
    Returns (trades_list, equity_curve, metrics_dict).
    """
    balance  = INITIAL_BALANCE
    pos      = None      # (entry_price, qty, sl, tp, fee_paid)
    trades   = []
    equity   = [balance]

    for i in range(len(df)):
        row   = df.iloc[i]
        price = float(row["close"])
        sig   = row["signal"]
        ts    = df.index[i]

        # Risk exits
        if pos:
            ep, qty, sl, tp, ef = pos
            hit_sl = price <= sl
            hit_tp = price >= tp
            if hit_sl or hit_tp:
                gross    = qty * price
                fee      = gross * FEE
                proceeds = gross - fee
                pnl      = proceeds - (ep * qty + ef)
                balance += proceeds
                tag      = "STOP-LOSS" if hit_sl else "TAKE-PROFIT"
                trades.append({"time": ts, "side": "SELL", "price": price,
                               "qty": qty, "pnl": pnl, "reason": tag,
                               "balance": balance})
                pos = None

        # Strategy signals
        if sig == "BUY" and pos is None:
            capital = balance * pos_pct
            fee     = capital * FEE
            qty     = (capital - fee) / price
            if qty > 0 and balance >= capital:
                balance -= capital
                sl_p = price * (1 - sl_pct)
                tp_p = price * (1 + tp_pct)
                pos  = (price, qty, sl_p, tp_p, fee)
                trades.append({"time": ts, "side": "BUY", "price": price,
                               "qty": qty, "pnl": 0.0, "reason": row["reason"],
                               "balance": balance})

        elif sig == "SELL" and pos is not None:
            ep, qty, sl, tp, ef = pos
            gross    = qty * price
            fee      = gross * FEE
            proceeds = gross - fee
            pnl      = proceeds - (ep * qty + ef)
            balance += proceeds
            trades.append({"time": ts, "side": "SELL", "price": price,
                           "qty": qty, "pnl": pnl, "reason": row["reason"],
                           "balance": balance})
            pos = None

        # Equity = cash + mark-to-market
        mtm = balance + (pos[1] * price if pos else 0)
        equity.append(mtm)

    # Close open position at last price
    if pos:
        last = float(df["close"].iloc[-1])
        ep, qty, sl, tp, ef = pos
        gross    = qty * last
        fee      = gross * FEE
        proceeds = gross - fee
        pnl      = proceeds - (ep * qty + ef)
        balance += proceeds
        trades.append({"time": df.index[-1], "side": "SELL", "price": last,
                       "qty": qty, "pnl": pnl, "reason": "END_OF_DATA",
                       "balance": balance})
        equity.append(balance)

    # Metrics
    sells     = [t for t in trades if t["side"] == "SELL"]
    wins      = [t["pnl"] for t in sells if t["pnl"] > 0]
    losses    = [t["pnl"] for t in sells if t["pnl"] <= 0]
    eq        = np.array(equity)
    run_max   = np.maximum.accumulate(eq)
    drawdowns = (run_max - eq) / run_max * 100
    eq_s      = pd.Series(equity)
    daily_ret = eq_s.pct_change().dropna()
    sharpe    = (float(daily_ret.mean() / daily_ret.std()) * math.sqrt(365)
                 if daily_ret.std() > 0 else 0.0)

    metrics = {
        "final_balance":   round(balance, 2),
        "total_return":    round((balance - INITIAL_BALANCE) / INITIAL_BALANCE * 100, 2),
        "total_trades":    len(trades),
        "win_trades":      len(wins),
        "loss_trades":     len(losses),
        "win_rate":        round(len(wins) / len(sells) * 100, 1) if sells else 0.0,
        "avg_win":         round(float(np.mean(wins)),   2) if wins   else 0.0,
        "avg_loss":        round(float(np.mean(losses)), 2) if losses else 0.0,
        "profit_factor":   round(sum(wins) / abs(sum(losses)), 4) if losses else float("inf"),
        "max_drawdown":    round(float(np.max(drawdowns)), 2) if len(drawdowns) else 0.0,
        "sharpe_ratio":    round(sharpe, 4),
    }
    return trades, equity, metrics


# ══════════════════════════════════════════════════════════════════════════════
#  CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e2e8f0",
    font_family="DM Sans, sans-serif",
    margin=dict(l=0, r=0, t=36, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e293b", borderwidth=1),
    xaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
    yaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
)


def price_rsi_chart(df: pd.DataFrame, pair: str,
                    show_bb: bool, show_ma: bool,
                    rsi_os: int, rsi_ob: int) -> go.Figure:
    """Dual-pane: candlestick + overlays on top, RSI on bottom."""
    sig_df = df[df["signal"] != "HOLD"]

    fig = make_subplots(
        rows=3, cols=1,
        row_heights=[0.55, 0.25, 0.20],
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=("", "", ""),
    )

    # ── Candlestick ───────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name=pair,
        increasing_line_color="#00ff88",
        decreasing_line_color="#ff4466",
        increasing_fillcolor="rgba(0,255,136,0.25)",
        decreasing_fillcolor="rgba(255,68,102,0.25)",
    ), row=1, col=1)

    # ── Bollinger Bands ───────────────────────────────────────────
    if show_bb and "bb_u" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["bb_u"], name="BB Upper",
            line=dict(color="#4fc3f7", width=1, dash="dot"), opacity=0.7,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["bb_l"], name="BB Lower",
            fill="tonexty", fillcolor="rgba(79,195,247,0.05)",
            line=dict(color="#4fc3f7", width=1, dash="dot"), opacity=0.7,
        ), row=1, col=1)

    # ── Moving averages ───────────────────────────────────────────
    if show_ma:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["sma_s"], name="SMA Short",
            line=dict(color="#ffd700", width=1.5),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["sma_l"], name="SMA Long",
            line=dict(color="#ff9f43", width=1.5),
        ), row=1, col=1)

    # ── Buy / Sell markers on price ───────────────────────────────
    buys  = sig_df[sig_df["signal"] == "BUY"]
    sells = sig_df[sig_df["signal"] == "SELL"]
    if not buys.empty:
        fig.add_trace(go.Scatter(
            x=buys.index, y=buys["low"] * 0.993,
            mode="markers", name="BUY",
            marker=dict(symbol="triangle-up", size=12,
                        color="#00ff88", line=dict(color="#00ff88", width=1)),
        ), row=1, col=1)
    if not sells.empty:
        fig.add_trace(go.Scatter(
            x=sells.index, y=sells["high"] * 1.007,
            mode="markers", name="SELL",
            marker=dict(symbol="triangle-down", size=12,
                        color="#ff4466", line=dict(color="#ff4466", width=1)),
        ), row=1, col=1)

    # ── Volume bars ───────────────────────────────────────────────
    colours = ["rgba(0,255,136,0.4)" if c >= o else "rgba(255,68,102,0.4)"
               for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["volume"],
        name="Volume", marker_color=colours, showlegend=False,
    ), row=2, col=1)

    # ── RSI ───────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=df.index, y=df["rsi"], name="RSI",
        line=dict(color="#a78bfa", width=2),
    ), row=3, col=1)
    fig.add_hline(y=rsi_ob, line_dash="dash", line_color="#ff4466",
                  line_width=1, opacity=0.6, row=3, col=1)
    fig.add_hline(y=rsi_os, line_dash="dash", line_color="#00ff88",
                  line_width=1, opacity=0.6, row=3, col=1)
    fig.add_hrect(y0=rsi_ob, y1=100, fillcolor="rgba(255,68,102,0.06)",
                  line_width=0, row=3, col=1)
    fig.add_hrect(y0=0, y1=rsi_os, fillcolor="rgba(0,255,136,0.06)",
                  line_width=0, row=3, col=1)

    fig.update_layout(
        **CHART_LAYOUT,
        height=620,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    return fig


def equity_chart(equity: list, trades: list) -> go.Figure:
    """Portfolio equity curve with trade markers."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=equity, mode="lines", name="Portfolio",
        line=dict(color="#00ff88", width=2.5),
        fill="tozeroy", fillcolor="rgba(0,255,136,0.07)",
    ))
    fig.add_hline(y=INITIAL_BALANCE, line_dash="dot",
                  line_color="#64748b", line_width=1,
                  annotation_text=f"Start ${INITIAL_BALANCE:,.0f}",
                  annotation_font_color="#64748b")
    fig.update_layout(
        **CHART_LAYOUT, height=320,
        xaxis_title="Candle Index",
        yaxis_title="Portfolio Value ($)",
    )
    return fig


def pnl_bar_chart(trades: list) -> go.Figure:
    sells = [t for t in trades if t["side"] == "SELL" and t["reason"] != "END_OF_DATA"]
    if not sells:
        return go.Figure()
    fig = go.Figure(go.Bar(
        x=[f"#{i+1}" for i in range(len(sells))],
        y=[t["pnl"] for t in sells],
        marker_color=["#00ff88" if t["pnl"] > 0 else "#ff4466" for t in sells],
        text=[f"${t['pnl']:+.0f}" for t in sells],
        textposition="outside",
    ))
    fig.add_hline(y=0, line_color="#64748b", line_width=1)
    fig.update_layout(**CHART_LAYOUT, height=260,
                      xaxis_title="Trade #", yaxis_title="PnL ($)")
    return fig


def csv_equity_chart(df: pd.DataFrame) -> go.Figure:
    """Reconstruct equity from CSV balance column."""
    bal_col = next((c for c in df.columns
                    if "balance" in c.lower()), None)
    if bal_col is None:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=df[bal_col], mode="lines+markers", name="Balance",
        line=dict(color="#4fc3f7", width=2),
        marker=dict(size=5, color="#4fc3f7"),
    ))
    fig.update_layout(**CHART_LAYOUT, height=280,
                      xaxis_title="Trade #", yaxis_title="Balance ($)")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════

def _ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

_ss("last_refresh", 0.0)
_ss("price_cache", {})


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px'>
      <span style='font-family:Space Mono;font-size:1.3rem;color:#00ff88;font-weight:700'>₿ CryptoBot Pro</span><br>
      <span style='color:#64748b;font-size:.8rem'>Paper Trading Simulator</span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    pair_label = st.selectbox("Trading Pair", list(PAIRS.keys()), index=0)
    coin_id    = PAIRS[pair_label]

    strategy   = st.selectbox("Strategy", ["MA Crossover", "RSI", "Combined"])

    st.markdown("**RSI Settings**")
    rsi_period = st.slider("RSI Period",     7, 28, 14)
    rsi_os     = st.slider("Oversold (BUY)", 20, 40, 30)
    rsi_ob     = st.slider("Overbought (SELL)", 60, 85, 70)

    st.markdown("**MA Settings**")
    ma_short = st.slider("SMA Short Period", 5,  30, 10)
    ma_long  = st.slider("SMA Long Period",  20, 100, 50)

    st.markdown("**Risk Management**")
    pos_pct  = st.slider("Position Size %",  5, 50, 20) / 100
    sl_pct   = st.slider("Stop-Loss %",      1, 10, 3)  / 100
    tp_pct   = st.slider("Take-Profit %",    2, 20, 6)  / 100

    st.markdown("**Chart Overlays**")
    show_bb  = st.checkbox("Bollinger Bands", value=True)
    show_ma  = st.checkbox("Moving Averages", value=True)

    data_days = st.slider("Data Window (days)", 30, 365, 90)

    st.divider()
    st.markdown(
        "<div style='color:#64748b;font-size:.75rem;text-align:center'>"
        "📡 Data: CoinGecko Free API<br>"
        "💸 No real money used<br>"
        "🔄 Prices refresh every 60s</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div class='hero'>
  <p class='hero-title'>₿ CryptoBot Pro Dashboard</p>
  <p class='hero-sub'>
    Live paper trading simulator · Strategy: <b style='color:#00ff88'>{strategy}</b> ·
    Pair: <b style='color:#4fc3f7'>{pair_label}</b> ·
    {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
  </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════

t1, t2, t3, t4, t5 = st.tabs([
    "📡 Live Market", "📊 Signals", "🧪 Backtest", "📂 CSV Upload", "ℹ️ Deploy Guide"
])


# ════════════════════════════════════════════════════════════════
#  TAB 1 — LIVE MARKET
# ════════════════════════════════════════════════════════════════
with t1:
    col_refresh, col_info = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()

    # ── Price ticker ──────────────────────────────────────────────
    price_data = fetch_price(coin_id)

    if price_data:
        price    = price_data.get("usd", 0)
        change24 = price_data.get("usd_24h_change", 0)
        vol24    = price_data.get("usd_24h_vol", 0)
        arrow    = "▲" if change24 >= 0 else "▼"
        clr      = "ticker-up" if change24 >= 0 else "ticker-down"

        st.markdown(f"""
        <div style='background:#111827;border:1px solid #1e293b;border-radius:14px;
                    padding:20px 28px;margin-bottom:20px;display:flex;
                    align-items:center;gap:24px'>
          <div>
            <div style='color:#64748b;font-size:.8rem;letter-spacing:2px;
                        text-transform:uppercase;margin-bottom:4px'>{pair_label} · LIVE</div>
            <span class='ticker'>${price:,.2f}</span>
          </div>
          <div>
            <span class='{clr}' style='font-family:Space Mono;font-size:1.2rem;font-weight:700'>
              {arrow} {abs(change24):.2f}%
            </span>
            <div style='color:#64748b;font-size:.8rem'>24h Change</div>
          </div>
          <div>
            <span style='font-family:Space Mono;font-size:1.1rem;color:#4fc3f7'>
              ${vol24/1e9:.2f}B
            </span>
            <div style='color:#64748b;font-size:.8rem'>24h Volume</div>
          </div>
          <div style='margin-left:auto;text-align:right'>
            <div style='color:#64748b;font-size:.75rem'>🟢 Live</div>
            <div style='color:#64748b;font-size:.7rem'>CoinGecko API</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Live price unavailable — showing synthetic data. CoinGecko may be rate-limiting.", icon="📡")
        price = 42_000.0

    # ── OHLCV + indicators ────────────────────────────────────────
    with st.spinner("Fetching market data…"):
        df_raw = fetch_ohlcv(coin_id, data_days)
        df     = enrich(df_raw, rsi_period, ma_short, ma_long)
        df     = generate_signals(df, strategy, rsi_os, rsi_ob)

    # ── Live signal badge ─────────────────────────────────────────
    last_sig  = df["signal"].iloc[-1]
    last_rsi  = df["rsi"].iloc[-1]
    last_smas = df["sma_s"].iloc[-1]
    last_smal = df["sma_l"].iloc[-1]

    sig_badge = {
        "BUY":  "<span class='sig-buy'>▲ BUY SIGNAL</span>",
        "SELL": "<span class='sig-sell'>▼ SELL SIGNAL</span>",
        "HOLD": "<span class='sig-hold'>◆ HOLD</span>",
    }.get(last_sig, "")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current RSI",    f"{last_rsi:.1f}",
              delta=f"{'Oversold' if last_rsi < rsi_os else 'Overbought' if last_rsi > rsi_ob else 'Neutral'}")
    c2.metric(f"SMA {ma_short}",  f"${last_smas:,.0f}")
    c3.metric(f"SMA {ma_long}",   f"${last_smal:,.0f}")
    c4.metric("Candles Loaded", f"{len(df):,}")

    st.markdown(f"**Current Signal:** {sig_badge} · Strategy: `{strategy}`",
                unsafe_allow_html=True)
    st.markdown("")

    # ── Main chart ────────────────────────────────────────────────
    st.plotly_chart(
        price_rsi_chart(df.tail(300), pair_label, show_bb, show_ma, rsi_os, rsi_ob),
        use_container_width=True,
    )

    # ── Recent candles table ──────────────────────────────────────
    with st.expander("📋 Recent Candles (last 20)"):
        recent = df[["open","high","low","close","rsi","sma_s","sma_l","signal"]]\
                   .tail(20).copy()
        recent.index = recent.index.strftime("%m-%d %H:%M")
        recent = recent.round(2)
        st.dataframe(recent, use_container_width=True)


# ════════════════════════════════════════════════════════════════
#  TAB 2 — SIGNALS
# ════════════════════════════════════════════════════════════════
with t2:
    st.subheader("📊 Buy / Sell Signal History")

    sig_df   = df[df["signal"] != "HOLD"].copy()
    sig_df.index = sig_df.index.strftime("%Y-%m-%d %H:%M")

    if sig_df.empty:
        st.info("No signals generated for the current settings. "
                "Try adjusting RSI thresholds or switching strategy.")
    else:
        # Stats row
        n_buy  = (sig_df["signal"] == "BUY").sum()
        n_sell = (sig_df["signal"] == "SELL").sum()

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Signals",  len(sig_df))
        s2.metric("BUY Signals",    n_buy,  delta=f"+{n_buy}")
        s3.metric("SELL Signals",   n_sell, delta=f"-{n_sell}", delta_color="inverse")
        s4.metric("Signal Ratio B/S", f"{n_buy}/{n_sell}")

        # Signal table with coloured badges
        display = sig_df[["close","rsi","sma_s","sma_l","signal","reason"]]\
                    .rename(columns={"close":"Price","rsi":"RSI",
                                     "sma_s":f"SMA{ma_short}",
                                     "sma_l":f"SMA{ma_long}",
                                     "signal":"Signal","reason":"Reason"})

        # Colour the Signal column
        def colour_signal(val):
            colours = {"BUY": "color:#00ff88;font-weight:700",
                       "SELL": "color:#ff4466;font-weight:700",
                       "HOLD": "color:#ffd700"}
            return colours.get(val, "")

        styled = display.style.applymap(colour_signal, subset=["Signal"])\
                              .format({"Price": "${:,.2f}", "RSI": "{:.1f}",
                                       f"SMA{ma_short}": "${:,.0f}",
                                       f"SMA{ma_long}":  "${:,.0f}"})
        st.dataframe(styled, use_container_width=True)

        # Download
        csv_bytes = display.to_csv().encode()
        st.download_button(
            "⬇️ Download Signals CSV", csv_bytes,
            file_name=f"signals_{pair_label.replace('/','-')}_{strategy.replace(' ','_')}.csv",
            mime="text/csv",
        )

        # Signal distribution pie
        pie_col, bar_col = st.columns(2)
        with pie_col:
            fig_pie = go.Figure(go.Pie(
                labels=["BUY","SELL"],
                values=[n_buy, n_sell],
                marker_colors=["#00ff88","#ff4466"],
                hole=0.5,
                textfont_size=14,
            ))
            fig_pie.update_layout(**CHART_LAYOUT, height=260,
                                  title="Signal Distribution")
            st.plotly_chart(fig_pie, use_container_width=True)

        with bar_col:
            # RSI distribution
            fig_rsi_hist = go.Figure(go.Histogram(
                x=df["rsi"].dropna(), nbinsx=30,
                marker_color="#a78bfa", opacity=0.8,
                name="RSI Distribution",
            ))
            fig_rsi_hist.add_vline(x=rsi_os, line_dash="dash",
                                   line_color="#00ff88", line_width=1.5)
            fig_rsi_hist.add_vline(x=rsi_ob, line_dash="dash",
                                   line_color="#ff4466", line_width=1.5)
            fig_rsi_hist.update_layout(**CHART_LAYOUT, height=260,
                                       title="RSI Distribution",
                                       xaxis_title="RSI Value",
                                       yaxis_title="Frequency")
            st.plotly_chart(fig_rsi_hist, use_container_width=True)


# ════════════════════════════════════════════════════════════════
#  TAB 3 — BACKTEST
# ════════════════════════════════════════════════════════════════
with t3:
    st.subheader("🧪 Strategy Backtester")
    st.caption(f"Simulating `{strategy}` on `{pair_label}` · "
               f"{data_days} days · ${INITIAL_BALANCE:,.0f} virtual capital")

    if st.button("🚀 Run Backtest", type="primary", use_container_width=False):
        with st.spinner("Running walk-forward simulation…"):
            trades, equity, metrics = run_backtest(df, pos_pct, sl_pct, tp_pct)
            st.session_state["bt_trades"] = trades
            st.session_state["bt_equity"] = equity
            st.session_state["bt_metrics"] = metrics

    if "bt_metrics" in st.session_state:
        m = st.session_state["bt_metrics"]
        trades  = st.session_state["bt_trades"]
        equity  = st.session_state["bt_equity"]

        # ── Metrics grid ──────────────────────────────────────────
        st.markdown("#### 📈 Performance Metrics")
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        ret_clr = "normal" if m["total_return"] >= 0 else "inverse"
        r1c1.metric("Total Return",   f"{m['total_return']:+.2f}%",
                    delta=f"${m['final_balance']-INITIAL_BALANCE:+,.0f}",
                    delta_color=ret_clr)
        r1c2.metric("Final Balance",  f"${m['final_balance']:,.2f}")
        r1c3.metric("Win Rate",       f"{m['win_rate']:.1f}%")
        r1c4.metric("Total Trades",   m["total_trades"])

        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        r2c1.metric("Profit Factor",  f"{m['profit_factor']:.3f}")
        r2c2.metric("Max Drawdown",   f"{m['max_drawdown']:.2f}%",
                    delta_color="inverse")
        r2c3.metric("Sharpe Ratio",   f"{m['sharpe_ratio']:.4f}")
        r2c4.metric("Avg Win / Loss",
                    f"${m['avg_win']:+.0f} / ${m['avg_loss']:+.0f}")

        # ── Colour-coded result banner ────────────────────────────
        if m["total_return"] >= 0:
            st.success(f"✅ Strategy PROFITABLE · Return: {m['total_return']:+.2f}% "
                       f"· Profit Factor: {m['profit_factor']:.2f}")
        else:
            st.error(f"❌ Strategy LOSS · Return: {m['total_return']:+.2f}% "
                     f"· Review settings and try again.")

        # ── Equity curve ──────────────────────────────────────────
        st.markdown("#### 📈 Equity Curve")
        st.plotly_chart(equity_chart(equity, trades), use_container_width=True)

        # ── PnL per trade bar chart ───────────────────────────────
        st.markdown("#### 💰 Realised PnL per Closed Trade")
        fig_pnl = pnl_bar_chart(trades)
        if fig_pnl.data:
            st.plotly_chart(fig_pnl, use_container_width=True)
        else:
            st.info("No closed trades yet.")

        # ── Trade log table ───────────────────────────────────────
        if trades:
            st.markdown("#### 📋 Trade Log")
            tdf = pd.DataFrame(trades)
            tdf["time"]  = tdf["time"].astype(str).str[:16]
            tdf["price"] = tdf["price"].map("${:,.2f}".format)
            tdf["pnl"]   = tdf["pnl"].map("${:+.2f}".format)
            tdf["balance"]= tdf["balance"].map("${:,.2f}".format)
            tdf.columns = ["Time","Side","Price","Qty","PnL","Reason","Balance"]

            def colour_side(val):
                if val == "BUY":  return "color:#00ff88;font-weight:700"
                if val == "SELL": return "color:#ff4466;font-weight:700"
                return ""

            styled_tdf = tdf.style.applymap(colour_side, subset=["Side"])
            st.dataframe(styled_tdf, use_container_width=True, hide_index=True)

            csv_trades = pd.DataFrame(st.session_state["bt_trades"])\
                           .to_csv(index=False).encode()
            st.download_button(
                "⬇️ Download Trade Log CSV", csv_trades,
                file_name=f"backtest_{pair_label.replace('/','-')}_{strategy.replace(' ','_')}.csv",
                mime="text/csv",
            )
    else:
        st.info("👆 Click **Run Backtest** to simulate the strategy on historical data.")
        st.markdown("""
        <div class='info-card'>
          <h4>What the backtest does</h4>
          <ul style='color:#94a3b8;line-height:1.9'>
            <li>Walks through every candle chronologically (no look-ahead bias)</li>
            <li>Executes BUY / SELL based on your chosen strategy</li>
            <li>Applies stop-loss, take-profit, and trading fees on each trade</li>
            <li>Tracks portfolio equity and computes Sharpe, drawdown, win-rate</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  TAB 4 — CSV UPLOAD
# ════════════════════════════════════════════════════════════════
with t4:
    st.subheader("📂 Backtest CSV Visualiser")
    st.caption("Upload any trade-log CSV (from the Backtest tab or the CLI bot) to visualise it here.")

    uploaded = st.file_uploader("Drop your CSV here", type=["csv"])

    if uploaded:
        csv_df = pd.read_csv(uploaded)
        st.success(f"Loaded {len(csv_df):,} rows · {len(csv_df.columns)} columns")

        with st.expander("🔍 Raw Data Preview", expanded=True):
            st.dataframe(csv_df.head(50), use_container_width=True)

        # Auto-detect numeric columns for charting
        num_cols = csv_df.select_dtypes(include=np.number).columns.tolist()

        # ── Equity / balance curve ────────────────────────────────
        bal_col = next((c for c in csv_df.columns if "balance" in c.lower()), None)
        if bal_col:
            st.markdown("#### 💼 Balance / Equity Curve")
            st.plotly_chart(csv_equity_chart(csv_df), use_container_width=True)

        # ── PnL bar chart ─────────────────────────────────────────
        pnl_col = next((c for c in csv_df.columns if "pnl" in c.lower()), None)
        if pnl_col:
            st.markdown("#### 💰 PnL per Trade")
            fig_csv_pnl = go.Figure(go.Bar(
                x=list(range(len(csv_df))),
                y=csv_df[pnl_col],
                marker_color=["#00ff88" if v >= 0 else "#ff4466"
                              for v in csv_df[pnl_col]],
            ))
            fig_csv_pnl.add_hline(y=0, line_color="#64748b")
            fig_csv_pnl.update_layout(**CHART_LAYOUT, height=260,
                                      xaxis_title="Trade #",
                                      yaxis_title="PnL ($)")
            st.plotly_chart(fig_csv_pnl, use_container_width=True)

        # ── Custom chart builder ──────────────────────────────────
        if num_cols:
            st.markdown("#### 🔧 Custom Chart Builder")
            cc1, cc2, cc3 = st.columns(3)
            x_col    = cc1.selectbox("X axis",     csv_df.columns.tolist())
            y_col    = cc2.selectbox("Y axis",     num_cols)
            chart_t  = cc3.selectbox("Chart type", ["Line","Bar","Scatter"])

            if chart_t == "Line":
                fig_c = px.line(csv_df,   x=x_col, y=y_col)
            elif chart_t == "Bar":
                fig_c = px.bar(csv_df,    x=x_col, y=y_col)
            else:
                fig_c = px.scatter(csv_df, x=x_col, y=y_col)

            fig_c.update_traces(marker_color="#4fc3f7", line_color="#4fc3f7")
            fig_c.update_layout(**CHART_LAYOUT, height=280)
            st.plotly_chart(fig_c, use_container_width=True)

        # ── Summary stats ─────────────────────────────────────────
        st.markdown("#### 📊 Column Statistics")
        st.dataframe(csv_df[num_cols].describe().round(4), use_container_width=True)

    else:
        st.markdown("""
        <div style='text-align:center;padding:60px 20px;border:2px dashed #1e293b;
                    border-radius:16px;color:#64748b'>
          <div style='font-size:3rem'>📂</div>
          <div style='font-size:1.1rem;margin-top:12px'>
            Drop a CSV file above to visualise it
          </div>
          <div style='font-size:.85rem;margin-top:8px'>
            Works with any trade log from the Backtest tab or the CLI bot
          </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  TAB 5 — DEPLOY GUIDE
# ════════════════════════════════════════════════════════════════
with t5:
    st.subheader("🚀 Deploy to Streamlit Cloud — Step by Step")
    st.caption("Get a public URL for this app in under 5 minutes. Free forever.")

    st.markdown("""
    <div class='step'>
      <div class='step-num'>Step 01 · GitHub</div>
      <b>Create a free GitHub account</b> at <a href='https://github.com' target='_blank'
      style='color:#4fc3f7'>github.com</a> if you don't have one.
    </div>

    <div class='step'>
      <div class='step-num'>Step 02 · New Repository</div>
      Click <b>New Repository</b> → name it <code>crypto-trading-bot</code> →
      set to <b>Public</b> → click <b>Create repository</b>.
    </div>

    <div class='step'>
      <div class='step-num'>Step 03 · Upload Files</div>
      Click <b>Add file → Upload files</b> and drag in these two files:<br><br>
      &nbsp;&nbsp;📄 <code>app.py</code> &nbsp;&nbsp; 📄 <code>requirements.txt</code><br><br>
      Then click <b>Commit changes</b>.
    </div>

    <div class='step'>
      <div class='step-num'>Step 04 · Streamlit Cloud</div>
      Go to <a href='https://share.streamlit.io' target='_blank'
      style='color:#4fc3f7'>share.streamlit.io</a> and sign in with your GitHub account.
    </div>

    <div class='step'>
      <div class='step-num'>Step 05 · Deploy</div>
      Click <b>New app</b> → select your <code>crypto-trading-bot</code> repo →
      set <b>Main file path</b> to <code>app.py</code> → click <b>Deploy!</b>
    </div>

    <div class='step'>
      <div class='step-num'>Step 06 · Your Public URL</div>
      In ~60 seconds you'll get a public URL like:<br><br>
      <code style='color:#00ff88'>https://your-username-crypto-trading-bot-app-xxxx.streamlit.app</code><br><br>
      Share it with anyone — no login required to view.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("#### 📁 Files Required for Deployment")

    fc1, fc2 = st.columns(2)
    with fc1:
        st.markdown("""
        <div class='info-card'>
          <h4>app.py</h4>
          <p style='color:#94a3b8;margin:0;font-size:.9rem'>
            The complete Streamlit app — everything in one file.<br>
            No external modules needed. ✅
          </p>
        </div>
        """, unsafe_allow_html=True)

    with fc2:
        st.markdown("""
        <div class='info-card'>
          <h4>requirements.txt</h4>
          <p style='color:#94a3b8;margin:0;font-size:.9rem'>
            <code>streamlit</code><br>
            <code>pandas</code><br>
            <code>numpy</code><br>
            <code>requests</code><br>
            <code>plotly</code>
          </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### ⚡ Optional: Dark Theme Config")
    st.markdown("""
    Create a folder called `.streamlit` and add `config.toml` inside it:
    """)
    st.code("""
[theme]
base                     = "dark"
primaryColor             = "#00ff88"
backgroundColor          = "#0a0e1a"
secondaryBackgroundColor = "#111827"
textColor                = "#e2e8f0"
font                     = "monospace"
    """, language="toml")

    st.markdown("#### 🛠️ Local Development")
    st.code("""
# 1. Clone your repo
git clone https://github.com/YOUR_USERNAME/crypto-trading-bot
cd crypto-trading-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run locally
streamlit run app.py

# App opens at → http://localhost:8501
    """, language="bash")

    st.markdown("#### ❓ Troubleshooting")
    with st.expander("CoinGecko rate limit / no live data"):
        st.markdown("""
        CoinGecko's free tier allows ~30 requests/minute.
        If you see "Live price unavailable", wait 60 seconds and click **Refresh**.
        The app automatically falls back to synthetic data so it never breaks.
        """)
    with st.expander("Deploy fails on Streamlit Cloud"):
        st.markdown("""
        - Make sure `requirements.txt` is in the **root** of the repo (same level as `app.py`)
        - Check the Streamlit Cloud logs for the exact error
        - Common fix: ensure `streamlit>=1.32.0` is listed in requirements
        """)
    with st.expander("How do I add my own strategy?"):
        st.markdown("""
        Find the `generate_signals()` function in `app.py` and add a new `elif strategy == "My Strategy":` block.
        Then add `"My Strategy"` to the `st.selectbox` list in the sidebar.
        """)

    st.divider()
    st.markdown("""
    <div style='text-align:center;color:#64748b;font-size:.85rem;padding:8px'>
      ⚠️ This is a <b>paper trading simulator</b> — no real money is involved.<br>
      Past simulated performance does not guarantee future results.
    </div>
    """, unsafe_allow_html=True)
