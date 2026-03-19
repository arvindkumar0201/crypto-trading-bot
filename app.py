"""
app.py  ·  CryptoBot Pro — Live Trading Dashboard
DATA : CoinAPI (rest.coinapi.io) · Key: 97a80274-06ba-46ab-87c6-996da6ac6650
CANDLES : 1-minute OHLCV (real Binance Spot trade data)
REFRESH : Every 10 seconds (auto)
"""
import math
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="CryptoBot Pro", page_icon="₿",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{--g:#00ff88;--r:#ff4466;--y:#ffd700;--b:#4fc3f7;--p:#a78bfa;
      --bg:#080c14;--card:#0e1420;--bdr:#1a2236;--mut:#4a5568;--txt:#e2e8f0;}
html,body,[data-testid="stAppViewContainer"]{background:var(--bg)!important;font-family:'DM Sans',sans-serif;}
[data-testid="stSidebar"]{background:#0a0d16!important;border-right:1px solid var(--bdr);}
[data-testid="metric-container"]{background:var(--card);border:1px solid var(--bdr);
  border-radius:10px;padding:14px 18px!important;transition:border-color .2s;}
[data-testid="metric-container"]:hover{border-color:var(--g);}
[data-testid="stMetricValue"]{font-family:'Space Mono',monospace!important;font-size:1.45rem!important;}
.stTabs [role="tablist"]{background:var(--card);border-radius:10px;padding:4px;
  border:1px solid var(--bdr);gap:3px;}
.stTabs [role="tab"]{border-radius:7px!important;color:var(--mut)!important;transition:all .2s;}
.stTabs [aria-selected="true"]{background:var(--g)!important;color:#000!important;font-weight:700;}
.stButton>button{background:transparent;border:1px solid var(--g);color:var(--g);
  font-family:'Space Mono',monospace;font-weight:700;border-radius:8px;transition:all .2s;}
.stButton>button:hover{background:var(--g);color:#000;}
.stButton>button[kind="primary"]{background:var(--g);color:#000;}
.hero{background:linear-gradient(135deg,#0e1420,#111827 60%,#0a1022);border:1px solid var(--bdr);
  border-radius:16px;padding:22px 26px;margin-bottom:18px;position:relative;overflow:hidden;}
.hero::after{content:'';position:absolute;top:-80px;right:-80px;width:220px;height:220px;
  background:radial-gradient(circle,rgba(0,255,136,.07) 0%,transparent 70%);border-radius:50%;pointer-events:none;}
.htitle{font-family:'Space Mono',monospace;font-size:1.65rem;font-weight:700;
  color:var(--g);margin:0 0 6px 0;letter-spacing:-.5px;}
.bigprice{font-family:'Space Mono',monospace;font-size:2.7rem;font-weight:700;letter-spacing:-1px;line-height:1;}
.up{color:var(--g);} .dn{color:var(--r);} .ne{color:var(--txt);}
.sig-buy{background:rgba(0,255,136,.1);color:var(--g);border:1px solid rgba(0,255,136,.3);
  padding:3px 13px;border-radius:20px;font-weight:700;font-size:.8rem;font-family:'Space Mono',monospace;}
.sig-sell{background:rgba(255,68,102,.1);color:var(--r);border:1px solid rgba(255,68,102,.3);
  padding:3px 13px;border-radius:20px;font-weight:700;font-size:.8rem;font-family:'Space Mono',monospace;}
.sig-hold{background:rgba(255,215,0,.08);color:var(--y);border:1px solid rgba(255,215,0,.25);
  padding:3px 13px;border-radius:20px;font-weight:700;font-size:.8rem;font-family:'Space Mono',monospace;}
.pill{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;
  font-family:'Space Mono',monospace;font-size:.73rem;font-weight:700;}
.plive{background:rgba(0,255,136,.08);border:1px solid rgba(0,255,136,.25);color:var(--g);}
.perr{background:rgba(255,68,102,.08);border:1px solid rgba(255,68,102,.25);color:var(--r);}
.pwrn{background:rgba(255,215,0,.07);border:1px solid rgba(255,215,0,.2);color:var(--y);}
.blink{animation:bl 1.4s ease-in-out infinite;}
@keyframes bl{0%,100%{opacity:1}50%{opacity:.2}}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px;}
</style>
""", unsafe_allow_html=True)

# ─── CoinAPI ──────────────────────────────────────────────────────────────────
API_KEY  = "97a80274-06ba-46ab-87c6-996da6ac6650"
API_BASE = "https://rest.coinapi.io/v1"
API_HDR  = {"X-CoinAPI-Key": API_KEY, "Accept": "application/json"}

PAIRS = {
    "BTC/USDT":  {"base":"BTC",  "quote":"USDT","sym":"BINANCE_SPOT_BTC_USDT"},
    "ETH/USDT":  {"base":"ETH",  "quote":"USDT","sym":"BINANCE_SPOT_ETH_USDT"},
    "SOL/USDT":  {"base":"SOL",  "quote":"USDT","sym":"BINANCE_SPOT_SOL_USDT"},
    "BNB/USDT":  {"base":"BNB",  "quote":"USDT","sym":"BINANCE_SPOT_BNB_USDT"},
    "XRP/USDT":  {"base":"XRP",  "quote":"USDT","sym":"BINANCE_SPOT_XRP_USDT"},
    "DOGE/USDT": {"base":"DOGE", "quote":"USDT","sym":"BINANCE_SPOT_DOGE_USDT"},
}
TIMEFRAMES = {
    "1 min":  {"period":"1MIN",  "limit":300, "label":"1-Minute"},
    "5 min":  {"period":"5MIN",  "limit":288, "label":"5-Minute"},
    "15 min": {"period":"15MIN", "limit":200, "label":"15-Minute"},
    "1 hour": {"period":"1HRS",  "limit":168, "label":"Hourly"},
    "4 hour": {"period":"4HRS",  "limit":120, "label":"4-Hour"},
    "1 day":  {"period":"1DAY",  "limit":365, "label":"Daily"},
}
INITIAL_BALANCE = 10_000.0
FEE = 0.001

# ─── API layer ────────────────────────────────────────────────────────────────
def _get(endpoint, params=None):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", headers=API_HDR,
                         params=params or {}, timeout=12)
        st.session_state.update({
            "api_status":  r.status_code,
            "api_ts":      datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        })
        if r.status_code == 200:
            st.session_state["api_ok"] = True
            st.session_state["api_err"] = ""
            return r.json()
        errors = {401:"Invalid API key",403:"Not authorised",
                  429:"Rate limit (free=100/day)",550:"No data"}
        st.session_state["api_ok"]  = False
        st.session_state["api_err"] = errors.get(r.status_code, f"HTTP {r.status_code}")
        return None
    except Exception as e:
        st.session_state.update({"api_ok":False,"api_err":str(e)[:70]})
        return None

@st.cache_data(ttl=8, show_spinner=False)
def fetch_spot(base, quote):
    return _get(f"/exchangerate/{base}/{quote}")

@st.cache_data(ttl=10, show_spinner=False)
def fetch_ohlcv(sym, period, limit):
    data = _get(f"/ohlcv/{sym}/latest", {"period_id":period,"limit":limit})
    if not data:
        return pd.DataFrame()
    rows = [{"ts":c["time_period_start"],"open":c["price_open"],"high":c["price_high"],
             "low":c["price_low"],"close":c["price_close"],"volume":c.get("volume_traded",0),
             "trades":c.get("trades_count",0)} for c in data]
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df.set_index("ts", inplace=True)
    df = df.astype(float)
    df.sort_index(inplace=True)
    return df

# ─── Indicators ───────────────────────────────────────────────────────────────
def rsi(s, n=14):
    d=s.diff(); g=d.clip(lower=0); l=-d.clip(upper=0)
    ag=g.ewm(com=n-1,min_periods=n).mean(); al=l.ewm(com=n-1,min_periods=n).mean()
    return 100-100/(1+ag/al.replace(0,np.nan))

def sma(s,n): return s.rolling(n).mean()
def ema(s,n): return s.ewm(span=n,adjust=False).mean()
def bb(s,n=20,std=2):
    m=sma(s,n); sg=s.rolling(n).std(); return m+std*sg, m, m-std*sg

def enrich(df, rsi_p=14, mas=9, mal=21):
    if df.empty: return df
    df=df.copy()
    df["rsi"]=rsi(df["close"],rsi_p)
    df["sma_s"]=sma(df["close"],mas); df["sma_l"]=sma(df["close"],mal)
    df["ema_s"]=ema(df["close"],mas); df["ema_l"]=ema(df["close"],mal)
    fast=ema(df["close"],12); slow=ema(df["close"],26)
    df["macd"]=fast-slow; df["macd_sig"]=ema(df["macd"],9)
    df["bb_u"],df["bb_m"],df["bb_l"]=bb(df["close"])
    return df

# ─── Signals ─────────────────────────────────────────────────────────────────
def signals(df, strategy, os=30, ob=70):
    if df.empty: return df
    df=df.copy(); sigs=[]; rsns=[]
    for i in range(len(df)):
        sig,rsn="HOLD","—"
        row=df.iloc[i]; prev=df.iloc[i-1] if i>0 else row
        if strategy=="MA Crossover":
            if pd.notna(row.get("sma_s")) and pd.notna(row.get("sma_l")):
                if prev["sma_s"]<=prev["sma_l"] and row["sma_s"]>row["sma_l"]:
                    sig,rsn="BUY",f"Golden Cross {df.index[i].strftime('%H:%M')}"
                elif prev["sma_s"]>=prev["sma_l"] and row["sma_s"]<row["sma_l"]:
                    sig,rsn="SELL",f"Death Cross {df.index[i].strftime('%H:%M')}"
        elif strategy=="RSI":
            if pd.notna(row.get("rsi")):
                if prev["rsi"]>=os and row["rsi"]<os: sig,rsn="BUY",f"RSI OS {row['rsi']:.1f}"
                elif row["rsi"]>ob: sig,rsn="SELL",f"RSI OB {row['rsi']:.1f}"
        elif strategy=="Combined":
            ma_b=ma_s2=rb=rs2=False
            if pd.notna(row.get("sma_s")):
                ma_b=prev["sma_s"]<=prev["sma_l"] and row["sma_s"]>row["sma_l"]
                ma_s2=prev["sma_s"]>=prev["sma_l"] and row["sma_s"]<row["sma_l"]
            if pd.notna(row.get("rsi")):
                rb=prev["rsi"]>=os and row["rsi"]<os
                rs2=row["rsi"]>ob
            if ma_b and rb: sig,rsn="BUY","Combined MA+RSI"
            if ma_s2 and rs2: sig,rsn="SELL","Combined MA+RSI"
        sigs.append(sig); rsns.append(rsn)
    df["signal"]=sigs; df["reason"]=rsns
    return df

# ─── Backtest ─────────────────────────────────────────────────────────────────
def backtest(df, pos_pct, sl_pct, tp_pct):
    if df.empty: return [],[INITIAL_BALANCE],{}
    bal=INITIAL_BALANCE; pos=None; trades=[]; eq=[bal]
    for i in range(len(df)):
        row=df.iloc[i]; price=float(row["close"]); sig=row.get("signal","HOLD")
        if pos:
            ep,qty,sl,tp,ef=pos
            if price<=sl or price>=tp:
                gross=qty*price; fee=gross*FEE; pnl=(gross-fee)-(ep*qty+ef)
                bal+=gross-fee; tag="SL" if price<=sl else "TP"
                trades.append({"time":df.index[i],"side":"SELL","price":price,
                               "qty":qty,"pnl":pnl,"reason":tag,"balance":bal})
                pos=None
        if sig=="BUY" and pos is None:
            cap=bal*pos_pct; fee=cap*FEE; qty=(cap-fee)/price
            if qty>0 and bal>=cap:
                bal-=cap; pos=(price,qty,price*(1-sl_pct),price*(1+tp_pct),fee)
                trades.append({"time":df.index[i],"side":"BUY","price":price,
                               "qty":qty,"pnl":0.,"reason":row.get("reason",""),"balance":bal})
        elif sig=="SELL" and pos is not None:
            ep,qty,sl,tp,ef=pos; gross=qty*price; fee=gross*FEE
            pnl=(gross-fee)-(ep*qty+ef); bal+=gross-fee
            trades.append({"time":df.index[i],"side":"SELL","price":price,
                           "qty":qty,"pnl":pnl,"reason":row.get("reason",""),"balance":bal})
            pos=None
        eq.append(bal+(pos[1]*price if pos else 0))
    if pos:
        lp=float(df["close"].iloc[-1]); ep,qty,sl,tp,ef=pos
        pnl=(qty*lp*(1-FEE))-(ep*qty+ef); bal+=qty*lp*(1-FEE)
        trades.append({"time":df.index[-1],"side":"SELL","price":lp,"qty":qty,
                       "pnl":pnl,"reason":"END","balance":bal}); eq.append(bal)
    sells=[t for t in trades if t["side"]=="SELL"]
    wins=[t["pnl"] for t in sells if t["pnl"]>0]
    losses=[t["pnl"] for t in sells if t["pnl"]<=0]
    eq_a=np.array(eq); rm=np.maximum.accumulate(eq_a)
    dd=(rm-eq_a)/rm*100
    eq_s=pd.Series(eq); ret=eq_s.pct_change().dropna()
    sharpe=float(ret.mean()/ret.std()*math.sqrt(525600) if ret.std()>0 else 0)
    return trades, eq, {
        "final_balance":round(bal,2),"total_return":round((bal-INITIAL_BALANCE)/INITIAL_BALANCE*100,2),
        "total_trades":len(trades),"win_trades":len(wins),"loss_trades":len(losses),
        "win_rate":round(len(wins)/len(sells)*100,1) if sells else 0,
        "avg_win":round(float(np.mean(wins)),2) if wins else 0,
        "avg_loss":round(float(np.mean(losses)),2) if losses else 0,
        "profit_factor":round(sum(wins)/abs(sum(losses)),3) if losses else 999,
        "max_drawdown":round(float(np.max(dd)),2),"sharpe_ratio":round(sharpe,3),
    }

# ─── Charts ───────────────────────────────────────────────────────────────────
LAY = dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
           font_color="#e2e8f0",font_family="DM Sans,sans-serif",
           margin=dict(l=0,r=0,t=30,b=0),hovermode="x unified",
           legend=dict(bgcolor="rgba(0,0,0,0)",bordercolor="#1a2236",
                       borderwidth=1,orientation="h",y=1.05),
           xaxis=dict(gridcolor="#1a2236",zerolinecolor="#1a2236",
                      showgrid=True,rangeslider_visible=False),
           yaxis=dict(gridcolor="#1a2236",zerolinecolor="#1a2236",showgrid=True))

def main_chart(df, pair, spot, show_bb, show_ema, os, ob, tflabel):
    if df.empty:
        fig=go.Figure(); fig.update_layout(**LAY,height=580)
        fig.add_annotation(text="⏳ Waiting for data from CoinAPI…",
                           xref="paper",yref="paper",x=.5,y=.5,
                           showarrow=False,font_size=16,font_color="#4a5568")
        return fig
    sig_df=df[df["signal"]!="HOLD"] if "signal" in df.columns else pd.DataFrame()
    fig=make_subplots(rows=3,cols=1,row_heights=[.55,.22,.23],
                      shared_xaxes=True,vertical_spacing=.03)
    # Candles
    fig.add_trace(go.Candlestick(
        x=df.index,open=df["open"],high=df["high"],low=df["low"],close=df["close"],
        name=pair,increasing_line_color="#00ff88",decreasing_line_color="#ff4466",
        increasing_fillcolor="rgba(0,255,136,.28)",decreasing_fillcolor="rgba(255,68,102,.28)",
        line_width=1),row=1,col=1)
    # Spot price line
    if spot and spot>0:
        fig.add_hline(y=spot,row=1,col=1,
                      line=dict(color="rgba(255,255,255,.3)",width=1,dash="dot"),
                      annotation_text=f" ${spot:,.2f} LIVE",
                      annotation_font_color="#e2e8f0",annotation_font_size=10)
    # BB
    if show_bb and "bb_u" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["bb_u"],name="BB↑",
            line=dict(color="rgba(79,195,247,.55)",width=1,dash="dot")),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["bb_l"],name="BB↓",
            fill="tonexty",fillcolor="rgba(79,195,247,.04)",
            line=dict(color="rgba(79,195,247,.55)",width=1,dash="dot"),showlegend=False),row=1,col=1)
    # EMA
    if show_ema and "ema_s" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["ema_s"],name=f"EMA S",
            line=dict(color="#ffd700",width=1.5)),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["ema_l"],name=f"EMA L",
            line=dict(color="#ff9f43",width=1.5)),row=1,col=1)
    # Signals
    if not sig_df.empty:
        buys=sig_df[sig_df["signal"]=="BUY"]; sells=sig_df[sig_df["signal"]=="SELL"]
        if not buys.empty:
            fig.add_trace(go.Scatter(x=buys.index,y=buys["low"]*.9985,mode="markers",
                name="BUY",marker=dict(symbol="triangle-up",size=11,color="#00ff88")),row=1,col=1)
        if not sells.empty:
            fig.add_trace(go.Scatter(x=sells.index,y=sells["high"]*1.0015,mode="markers",
                name="SELL",marker=dict(symbol="triangle-down",size=11,color="#ff4466")),row=1,col=1)
    # Volume
    vc=["rgba(0,255,136,.42)" if c>=o else "rgba(255,68,102,.42)"
        for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df.index,y=df["volume"],marker_color=vc,
                         name="Vol",showlegend=False),row=2,col=1)
    # RSI
    fig.add_trace(go.Scatter(x=df.index,y=df["rsi"],name="RSI",
        line=dict(color="#a78bfa",width=2),
        fill="tozeroy",fillcolor="rgba(167,139,250,.05)"),row=3,col=1)
    fig.add_hline(y=ob,line_dash="dash",line_color="rgba(255,68,102,.6)",line_width=1,row=3,col=1,
                  annotation_text=f"OB {ob}",annotation_font_size=9,annotation_font_color="#ff4466")
    fig.add_hline(y=os,line_dash="dash",line_color="rgba(0,255,136,.6)",line_width=1,row=3,col=1,
                  annotation_text=f"OS {os}",annotation_font_size=9,annotation_font_color="#00ff88")
    fig.add_hrect(y0=ob,y1=100,fillcolor="rgba(255,68,102,.04)",line_width=0,row=3,col=1)
    fig.add_hrect(y0=0,y1=os,fillcolor="rgba(0,255,136,.04)",line_width=0,row=3,col=1)
    fig.update_layout(**LAY,height=610,
        title=dict(text=f"<b>{pair}</b>  ·  {tflabel} Candles  ·  Real Binance Data via CoinAPI",
                   font=dict(size=12,color="#4a5568"),x=0,xanchor="left"))
    fig.update_yaxes(title_text="Price (USDT)",row=1,col=1,title_font_size=10)
    fig.update_yaxes(title_text="Volume",      row=2,col=1,title_font_size=10)
    fig.update_yaxes(title_text="RSI",range=[0,100],row=3,col=1,title_font_size=10)
    return fig

def equity_fig(eq):
    fig=go.Figure()
    fig.add_trace(go.Scatter(y=eq,mode="lines",name="Equity",
        line=dict(color="#00ff88",width=2.5),
        fill="tozeroy",fillcolor="rgba(0,255,136,.06)"))
    fig.add_hline(y=INITIAL_BALANCE,line_dash="dot",line_color="#4a5568",
                  annotation_text=f"Start ${INITIAL_BALANCE:,.0f}",annotation_font_size=10,
                  annotation_font_color="#4a5568")
    fig.update_layout(**LAY,height=280,xaxis_title="Candle",yaxis_title="Portfolio ($)")
    return fig

def pnl_fig(trades):
    sells=[t for t in trades if t["side"]=="SELL" and t["reason"]!="END"]
    if not sells: return go.Figure()
    fig=go.Figure(go.Bar(
        x=[f"T{i+1}" for i in range(len(sells))],
        y=[t["pnl"] for t in sells],
        marker_color=["#00ff88" if t["pnl"]>0 else "#ff4466" for t in sells],
        text=[f"${t['pnl']:+.0f}" for t in sells],textposition="outside",textfont_size=10))
    fig.add_hline(y=0,line_color="#4a5568")
    fig.update_layout(**LAY,height=230,xaxis_title="Trade",yaxis_title="PnL ($)")
    return fig

def sparkline_fig(ph):
    fig=go.Figure()
    clrs=["#00ff88","#4fc3f7","#ffd700","#a78bfa","#ff9f43","#ff4466"]
    for i,(p,v) in enumerate(ph.items()):
        if len(v)<2: continue
        b=v[0]; pcts=[(x-b)/b*100 for x in v]
        fig.add_trace(go.Scatter(y=pcts,name=p,
                                 line=dict(color=clrs[i%len(clrs)],width=2)))
    fig.add_hline(y=0,line_dash="dot",line_color="#4a5568",line_width=1)
    fig.update_layout(**LAY,height=240,
                      yaxis_title="% Change since load",xaxis_title="10s ticks")
    return fig

# ─── Session state ────────────────────────────────────────────────────────────
for k,v in [("api_ok",None),("api_status","—"),("api_ts","—"),
            ("api_err",""),("refresh_count",0),
            ("prices_hist",{}),("bt_results",None),
            ("bt_trades",[]),("bt_equity",[])]:
    if k not in st.session_state: st.session_state[k]=v

# ─── AUTO-REFRESH every 10 seconds ───────────────────────────────────────────
tick = st_autorefresh(interval=10_000, limit=None, key="ca_refresh")
st.session_state["refresh_count"] = tick

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='padding:12px 0 8px;text-align:center'>"
                "<span style='font-family:Space Mono,monospace;font-size:1.2rem;"
                "color:#00ff88;font-weight:700'>₿ CryptoBot Pro</span><br>"
                "<span style='color:#4a5568;font-size:.73rem'>CoinAPI · 10s Live</span>"
                "</div>",unsafe_allow_html=True)
    st.divider()
    pair_label = st.selectbox("Pair", list(PAIRS.keys()))
    pc = PAIRS[pair_label]
    timeframe  = st.selectbox("Candle Timeframe", list(TIMEFRAMES.keys()), index=0)
    tfc = TIMEFRAMES[timeframe]
    strategy   = st.selectbox("Strategy", ["MA Crossover","RSI","Combined"])
    st.markdown("**RSI**")
    rsi_p = st.slider("RSI Period",   7,28,14)
    rsi_os= st.slider("Oversold",    15,40,30)
    rsi_ob= st.slider("Overbought",  60,85,70)
    st.markdown("**EMA**")
    ma_s = st.slider("Short",  3,30, 9)
    ma_l = st.slider("Long",  10,100,21)
    st.markdown("**Risk (Backtest)**")
    pos_pct = st.slider("Position %", 5,50,20)/100
    sl_pct  = st.slider("Stop-Loss %",1,10, 3)/100
    tp_pct  = st.slider("Take-Profit %",2,20,6)/100
    st.markdown("**Overlays**")
    show_bb  = st.checkbox("Bollinger Bands",True)
    show_ema = st.checkbox("EMA Lines",True)
    st.divider()

    # Connection status
    ok=st.session_state.get("api_ok"); rc=st.session_state.get("refresh_count",0)
    s=st.session_state.get("api_status","—"); ts=st.session_state.get("api_ts","—")
    err=st.session_state.get("api_err","")
    dc="#00ff88" if ok is True else ("#ff4466" if ok is False else "#ffd700")
    lb="LIVE · COINAPI" if ok is True else ("ERROR" if ok is False else "CONNECTING…")
    bg="#0d2b1a" if ok is True else ("#2b0d1a" if ok is False else "#1a1a0a")
    st.markdown(f"""
    <div style='background:{bg};border:1px solid {dc}30;border-radius:10px;padding:12px 14px'>
      <div style='display:flex;align-items:center;gap:7px;margin-bottom:8px'>
        <span style='width:8px;height:8px;border-radius:50%;background:{dc};
                     box-shadow:0 0 8px {dc};display:inline-block' class='blink'></span>
        <span style='color:{dc};font-family:Space Mono,monospace;font-size:.78rem;font-weight:700'>{lb}</span>
      </div>
      <div style='color:#94a3b8;font-size:.72rem;line-height:1.9'>
        🔑 <code style='color:#ffd700;font-size:.69rem'>97a80274…6650</code><br>
        📡 HTTP: <b style='color:#e2e8f0'>{s}</b><br>
        🕐 Last: <b style='color:#e2e8f0'>{ts}</b><br>
        🔄 Tick #{rc} · auto 10s<br>
        📊 {tfc["label"]} · {pair_label}<br>
        {f'⚠️ <span style="color:#ff4466">{err}</span>' if err else '💸 Paper trades only'}
      </div>
    </div>""",unsafe_allow_html=True)
    st.markdown("")
    if st.button("🗑 Clear Cache + Refresh",use_container_width=True):
        st.cache_data.clear(); st.rerun()

# ─── Hero ─────────────────────────────────────────────────────────────────────
now=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
ok=st.session_state.get("api_ok"); rc=st.session_state.get("refresh_count",0)
dc="#00ff88" if ok is True else ("#ff4466" if ok is False else "#ffd700")
lb="LIVE · COINAPI" if ok is True else ("API ERROR" if ok is False else "CONNECTING…")
pc2="plive" if ok is True else ("perr" if ok is False else "pwrn")
st.markdown(f"""
<div class='hero'>
  <p class='htitle'>₿ CryptoBot Pro</p>
  <div style='display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:8px'>
    <span class='pill {pc2}'>
      <span style='width:7px;height:7px;border-radius:50%;background:{dc};
                   box-shadow:0 0 6px {dc};display:inline-block' class='blink'></span>
      {lb}
    </span>
    <span style='background:#0e1420;border:1px solid #1a2236;border-radius:20px;
                 padding:4px 12px;font-size:.73rem;font-family:Space Mono,monospace;color:#4a5568'>
      🕐 {now}
    </span>
    <span style='background:#0e1420;border:1px solid #1a2236;border-radius:20px;
                 padding:4px 12px;font-size:.73rem;font-family:Space Mono,monospace;color:#ffd700'>
      🔄 Tick #{rc} · 10s auto
    </span>
    <span style='background:#0e1420;border:1px solid #1a2236;border-radius:20px;
                 padding:4px 12px;font-size:.73rem;font-family:Space Mono,monospace;color:#4fc3f7'>
      📊 {tfc["label"]} · {pair_label} · Binance Spot
    </span>
  </div>
</div>""",unsafe_allow_html=True)

# ─── Tabs ─────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5 = st.tabs(["📡 Live Market","📊 Signals","🧪 Backtest","📂 CSV Upload","ℹ️ Deploy Guide"])

# ══ TAB 1 ═════════════════════════════════════════════════════════════════════
with t1:
    spot_data = fetch_spot(pc["base"], pc["quote"])
    spot_price = float(spot_data["rate"]) if spot_data else 0.0
    spot_time  = (spot_data["time"][:19].replace("T"," ")+" UTC") if spot_data else "—"

    # API error banner
    if st.session_state.get("api_ok") is False:
        st.error(f"**CoinAPI Error:** {st.session_state.get('api_err','')}  |  "
                 f"HTTP {st.session_state.get('api_status','—')}  |  "
                 "Free plan = 100 req/day — may be exhausted", icon="🔴")

    # Price history tracking
    ph = st.session_state["prices_hist"]
    if pair_label not in ph: ph[pair_label]=[]
    if spot_price>0:
        ph[pair_label].append(spot_price)
        ph[pair_label] = ph[pair_label][-180:]   # 30 min at 10s ticks
    hist = ph.get(pair_label,[spot_price or 1])
    first= hist[0] if hist else (spot_price or 1)
    sess_chg = (spot_price-first)/first*100 if first else 0
    s_arr = "▲" if sess_chg>=0 else "▼"
    s_clr = "#00ff88" if sess_chg>=0 else "#ff4466"

    if spot_price>0:
        # Session high/low
        s_hi = max(hist); s_lo = min(hist)
        st.markdown(f"""
        <div style='background:#0e1420;border:1px solid #1a2236;
                    border-radius:14px;padding:20px 26px;margin-bottom:16px'>
          <div style='display:flex;align-items:center;gap:30px;flex-wrap:wrap'>
            <div>
              <div style='color:#4a5568;font-size:.72rem;letter-spacing:2px;
                          text-transform:uppercase;margin-bottom:6px'>
                {pair_label} · COINAPI LIVE RATE
              </div>
              <span class='bigprice ne'>${spot_price:,.4f}</span>
            </div>
            <div>
              <div style='color:#4a5568;font-size:.7rem;text-transform:uppercase;
                          letter-spacing:1px;margin-bottom:4px'>Session Change</div>
              <span style='font-family:Space Mono,monospace;font-size:1.35rem;
                           color:{s_clr};font-weight:700'>{s_arr} {abs(sess_chg):.3f}%</span>
            </div>
            <div>
              <div style='color:#4a5568;font-size:.7rem;text-transform:uppercase;margin-bottom:4px'>Session H / L</div>
              <span style='font-family:Space Mono,monospace;color:#4fc3f7;font-size:.9rem'>
                ${s_hi:,.4f} / ${s_lo:,.4f}
              </span>
            </div>
            <div>
              <div style='color:#4a5568;font-size:.7rem;text-transform:uppercase;margin-bottom:4px'>Ticks / Points</div>
              <span style='font-family:Space Mono,monospace;color:#a78bfa;font-size:.9rem'>
                {len(hist)} ticks · {len(hist)*10}s data
              </span>
            </div>
            <div>
              <div style='color:#4a5568;font-size:.7rem;text-transform:uppercase;margin-bottom:4px'>Last Updated</div>
              <span style='font-family:Space Mono,monospace;color:#64748b;font-size:.82rem'>{spot_time}</span>
            </div>
            <div style='margin-left:auto'>
              <span class='pill plive'>
                <span style='width:7px;height:7px;border-radius:50%;background:#00ff88;
                             box-shadow:0 0 6px #00ff88;display:inline-block' class='blink'></span>
                LIVE · 10s
              </span>
            </div>
          </div>
        </div>""",unsafe_allow_html=True)
    else:
        st.warning("⏳ Waiting for first price tick from CoinAPI…", icon="📡")

    # Load candles
    with st.spinner(f"Loading {tfc['label']} candles ({tfc['limit']} bars)…"):
        df_raw = fetch_ohlcv(pc["sym"], tfc["period"], tfc["limit"])
        df     = enrich(df_raw, rsi_p, ma_s, ma_l)
        df     = signals(df, strategy, rsi_os, rsi_ob)

    if not df.empty:
        last_rsi  = df["rsi"].iloc[-1]   if "rsi"   in df.columns else float("nan")
        last_es   = df["ema_s"].iloc[-1] if "ema_s" in df.columns else float("nan")
        last_el   = df["ema_l"].iloc[-1] if "ema_l" in df.columns else float("nan")
        last_sig  = df["signal"].iloc[-1] if "signal" in df.columns else "HOLD"
        last_c    = float(df["close"].iloc[-1])
        last_ts   = df.index[-1].strftime("%m-%d %H:%M")

        sig_badge={"BUY":"<span class='sig-buy'>▲ BUY</span>",
                   "SELL":"<span class='sig-sell'>▼ SELL</span>",
                   "HOLD":"<span class='sig-hold'>◆ HOLD</span>"}.get(last_sig,"")
        rsi_lbl=("🔴 OB" if last_rsi>rsi_ob else "🟢 OS" if last_rsi<rsi_os else "🟡 Neutral")

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("RSI",          f"{last_rsi:.1f}",    delta=rsi_lbl)
        c2.metric("Live Price",   f"${spot_price:,.4f}" if spot_price else "—")
        c3.metric("Last Candle",  f"${last_c:,.4f}",    delta=f"@ {last_ts}")
        c4.metric(f"EMA {ma_s}",  f"${last_es:,.2f}"   if not np.isnan(last_es) else "—")
        c5.metric(f"EMA {ma_l}",  f"${last_el:,.2f}"   if not np.isnan(last_el) else "—")

        st.markdown(f"**Signal:** {sig_badge} &nbsp;·&nbsp; `{strategy}` "
                    f"&nbsp;·&nbsp; **{len(df):,}** real candles &nbsp;·&nbsp; "
                    f"{'🟢 CoinAPI live data' if st.session_state.get('api_ok') else '🔴 No live data'}",
                    unsafe_allow_html=True)
        st.markdown("")
    else:
        st.warning("No candle data yet — CoinAPI loading…", icon="⏳")

    # Main chart
    st.plotly_chart(
        main_chart(df, pair_label, spot_price, show_bb, show_ema, rsi_os, rsi_ob, tfc["label"]),
        use_container_width=True,
    )

    # Sparkline for all-pairs session tracker
    if any(len(v)>2 for v in ph.values()):
        with st.expander("📈 Session Price Tracker — all pairs (% change since load)"):
            st.plotly_chart(sparkline_fig(ph), use_container_width=True)

    # Candle table
    with st.expander(f"🕯 Last {min(30,len(df))} {tfc['label']} Candles"):
        if not df.empty:
            sh=[c for c in ["open","high","low","close","volume","rsi","ema_s","ema_l","signal"] if c in df.columns]
            recent=df[sh].tail(30).copy()
            recent.index=recent.index.strftime("%m-%d %H:%M")
            st.dataframe(recent.round(4),use_container_width=True)

# ══ TAB 2 ═════════════════════════════════════════════════════════════════════
with t2:
    st.subheader("📊 Signal Log")
    st.caption(f"{strategy} · {pair_label} · {tfc['label']} · OS={rsi_os} OB={rsi_ob}")
    if df.empty:
        st.info("Waiting for data…")
    else:
        sdf=df[df["signal"]!="HOLD"].copy() if "signal" in df.columns else pd.DataFrame()
        nb=(sdf["signal"]=="BUY").sum() if not sdf.empty else 0
        ns=(sdf["signal"]=="SELL").sum() if not sdf.empty else 0
        s1,s2,s3,s4=st.columns(4)
        s1.metric("Total",len(sdf) if not sdf.empty else 0)
        s2.metric("BUY",nb,delta=f"+{nb}")
        s3.metric("SELL",ns,delta=f"-{ns}",delta_color="inverse")
        s4.metric("Ratio",f"{nb}:{ns}")
        if sdf.empty:
            st.info("No signals — adjust RSI thresholds or switch strategy.")
        else:
            sdf.index=sdf.index.strftime("%Y-%m-%d %H:%M")
            cols=[c for c in ["close","rsi","ema_s","ema_l","signal","reason"] if c in sdf.columns]
            disp=sdf[cols].rename(columns={"close":"Price","rsi":"RSI",
                "ema_s":f"EMA{ma_s}","ema_l":f"EMA{ma_l}","signal":"Signal","reason":"Reason"})
            def _sc(v): return {"BUY":"color:#00ff88;font-weight:700",
                                "SELL":"color:#ff4466;font-weight:700"}.get(v,"")
            fmt={"Price":"${:,.4f}","RSI":"{:.1f}"}
            if f"EMA{ma_s}" in disp.columns: fmt[f"EMA{ma_s}"]="${:,.2f}"
            if f"EMA{ma_l}" in disp.columns: fmt[f"EMA{ma_l}"]="${:,.2f}"
            st.dataframe(disp.style.applymap(_sc,subset=["Signal"]).format(fmt),
                         use_container_width=True)
            st.download_button("⬇️ CSV",disp.to_csv().encode(),
                               file_name=f"signals_{pair_label.replace('/','-')}.csv",mime="text/csv")
        p1,p2=st.columns(2)
        with p1:
            fig_pie=go.Figure(go.Pie(labels=["BUY","SELL"],
                values=[max(nb,.01),max(ns,.01)],marker_colors=["#00ff88","#ff4466"],
                hole=.55,textfont_size=13))
            fig_pie.update_layout(**LAY,height=230,title="Signal Split")
            st.plotly_chart(fig_pie,use_container_width=True)
        with p2:
            fig_rh=go.Figure(go.Histogram(x=df["rsi"].dropna(),nbinsx=28,
                marker_color="#a78bfa",opacity=.8))
            fig_rh.add_vline(x=rsi_os,line_dash="dash",line_color="#00ff88",line_width=1.5)
            fig_rh.add_vline(x=rsi_ob,line_dash="dash",line_color="#ff4466",line_width=1.5)
            fig_rh.update_layout(**LAY,height=230,title="RSI Distribution",
                                 xaxis_title="RSI",yaxis_title="Freq")
            st.plotly_chart(fig_rh,use_container_width=True)

# ══ TAB 3 ═════════════════════════════════════════════════════════════════════
with t3:
    st.subheader("🧪 Backtest")
    st.caption(f"Uses real {tfc['label']} candles already loaded · {len(df):,} bars")
    if st.button("🚀 Run Backtest",type="primary"):
        if df.empty: st.error("No data — wait for Live tab to load.")
        else:
            with st.spinner("Simulating…"):
                tl,eq,m=backtest(df,pos_pct,sl_pct,tp_pct)
                st.session_state.update({"bt_trades":tl,"bt_equity":eq,"bt_results":m})
    m=st.session_state.get("bt_results")
    if m:
        tl=st.session_state["bt_trades"]; eq=st.session_state["bt_equity"]
        rc2="normal" if m["total_return"]>=0 else "inverse"
        r1,r2,r3,r4=st.columns(4)
        r1.metric("Return",f"{m['total_return']:+.2f}%",
                  delta=f"${m['final_balance']-INITIAL_BALANCE:+,.0f}",delta_color=rc2)
        r2.metric("Balance",f"${m['final_balance']:,.2f}")
        r3.metric("Win Rate",f"{m['win_rate']:.1f}%")
        r4.metric("Trades",m["total_trades"])
        r5,r6,r7,r8=st.columns(4)
        r5.metric("Profit Factor",f"{m['profit_factor']:.3f}")
        r6.metric("Max Drawdown",f"{m['max_drawdown']:.2f}%",delta_color="inverse")
        r7.metric("Sharpe",f"{m['sharpe_ratio']:.3f}")
        r8.metric("W/L",f"{m['win_trades']}/{m['loss_trades']}")
        (st.success if m["total_return"]>=0 else st.error)(
            f"{'✅' if m['total_return']>=0 else '❌'} "
            f"{m['total_return']:+.2f}% · PF {m['profit_factor']:.2f} · WR {m['win_rate']:.1f}%")
        st.plotly_chart(equity_fig(eq),use_container_width=True)
        fp=pnl_fig(tl)
        if fp.data: st.plotly_chart(fp,use_container_width=True)
        if tl:
            tdf2=pd.DataFrame(tl)
            tdf2["time"]=tdf2["time"].astype(str).str[:16]
            tdf2["price"]=tdf2["price"].map("${:,.4f}".format)
            tdf2["pnl"]=tdf2["pnl"].map("${:+.2f}".format)
            tdf2["balance"]=tdf2["balance"].map("${:,.2f}".format)
            tdf2.columns=["Time","Side","Price","Qty","PnL","Reason","Balance"]
            def _cs2(v): return "color:#00ff88;font-weight:700" if v=="BUY" else \
                                "color:#ff4466;font-weight:700" if v=="SELL" else ""
            st.dataframe(tdf2.style.applymap(_cs2,subset=["Side"]),
                         use_container_width=True,hide_index=True)
            st.download_button("⬇️ CSV",pd.DataFrame(tl).to_csv(index=False).encode(),
                               file_name=f"bt_{pair_label.replace('/','-')}.csv",mime="text/csv")
    else:
        st.info("Click **Run Backtest** to simulate on real candles.")

# ══ TAB 4 ═════════════════════════════════════════════════════════════════════
with t4:
    st.subheader("📂 CSV Visualiser")
    up=st.file_uploader("Drop CSV",type=["csv"])
    if up:
        cdf=pd.read_csv(up)
        st.success(f"{len(cdf):,} rows · {len(cdf.columns)} columns")
        with st.expander("Raw Data",expanded=True): st.dataframe(cdf.head(50),use_container_width=True)
        nc=cdf.select_dtypes(include=np.number).columns.tolist()
        bc=next((c for c in cdf.columns if "balance" in c.lower()),None)
        if bc:
            fg=go.Figure(go.Scatter(y=cdf[bc],mode="lines+markers",
                line=dict(color="#4fc3f7",width=2),marker=dict(size=4)))
            fg.update_layout(**LAY,height=250,yaxis_title="Balance ($)")
            st.plotly_chart(fg,use_container_width=True)
        pc3=next((c for c in cdf.columns if "pnl" in c.lower()),None)
        if pc3:
            fp2=go.Figure(go.Bar(x=list(range(len(cdf))),y=cdf[pc3],
                marker_color=["#00ff88" if v>=0 else "#ff4466" for v in cdf[pc3]]))
            fp2.add_hline(y=0,line_color="#4a5568")
            fp2.update_layout(**LAY,height=230,yaxis_title="PnL ($)")
            st.plotly_chart(fp2,use_container_width=True)
        if nc:
            cc1,cc2,cc3=st.columns(3)
            xc=cc1.selectbox("X",cdf.columns.tolist())
            yc=cc2.selectbox("Y",nc)
            ct=cc3.selectbox("Type",["Line","Bar","Scatter"])
            fc=(px.line if ct=="Line" else px.bar if ct=="Bar" else px.scatter)(cdf,x=xc,y=yc)
            fc.update_traces(marker_color="#4fc3f7",line_color="#4fc3f7")
            fc.update_layout(**LAY,height=250)
            st.plotly_chart(fc,use_container_width=True)
        st.dataframe(cdf[nc].describe().round(4),use_container_width=True)
    else:
        st.markdown("<div style='text-align:center;padding:50px;border:2px dashed #1a2236;"
                    "border-radius:14px;color:#4a5568'><div style='font-size:2.5rem'>📂</div>"
                    "<div style='margin-top:10px'>Drop a CSV to visualise</div></div>",
                    unsafe_allow_html=True)

# ══ TAB 5 ═════════════════════════════════════════════════════════════════════
with t5:
    st.subheader("🚀 Deploy to Streamlit Cloud")
    st.markdown("""
    <div style='background:#0e1420;border-left:3px solid #00ff88;
                border-radius:0 10px 10px 0;padding:14px 18px;margin:10px 0'>
      <div style='color:#00ff88;font-family:Space Mono,monospace;font-size:.75rem;
                  font-weight:700;letter-spacing:1px;margin-bottom:6px'>STEP 01</div>
      Create repo at <code>github.com/new</code> → name <code>crypto-trading-bot</code> → Public
    </div>
    <div style='background:#0e1420;border-left:3px solid #00ff88;
                border-radius:0 10px 10px 0;padding:14px 18px;margin:10px 0'>
      <div style='color:#00ff88;font-family:Space Mono,monospace;font-size:.75rem;
                  font-weight:700;letter-spacing:1px;margin-bottom:6px'>STEP 02</div>
      Upload <code>app.py</code> + <code>requirements.txt</code> → Commit
    </div>
    <div style='background:#0e1420;border-left:3px solid #00ff88;
                border-radius:0 10px 10px 0;padding:14px 18px;margin:10px 0'>
      <div style='color:#00ff88;font-family:Space Mono,monospace;font-size:.75rem;
                  font-weight:700;letter-spacing:1px;margin-bottom:6px'>STEP 03</div>
      <a href='https://share.streamlit.io' target='_blank' style='color:#4fc3f7'>share.streamlit.io</a>
      → New app → <code>arvindkumar0201/crypto-trading-bot</code> → main file: <code>app.py</code> → Deploy!
    </div>
    <div style='background:#0d2b1a;border-left:3px solid #ffd700;
                border-radius:0 10px 10px 0;padding:14px 18px;margin:10px 0'>
      <div style='color:#ffd700;font-family:Space Mono,monospace;font-size:.75rem;
                  font-weight:700;letter-spacing:1px;margin-bottom:6px'>YOUR URL</div>
      <code style='color:#00ff88'>https://arvindkumar0201-crypto-trading-bot-app-xxxx.streamlit.app</code>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### requirements.txt")
    st.code("streamlit>=1.32.0\npandas>=2.0.0\nnumpy>=1.24.0\nrequests>=2.31.0\n"
            "plotly>=5.18.0\nstreamlit-autorefresh>=0.0.1", language="text")

    st.markdown("#### Run locally")
    st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")

    with st.expander("⚠️ CoinAPI rate limits"):
        st.markdown("""
**Free plan: 100 requests/day.**

With 10s auto-refresh and 2 API calls per tick:
- ~2,160 calls/day needed for 24h continuous use
- **Free plan runs for ~8 minutes** before hitting the limit

**Solutions:**
- Upgrade CoinAPI plan at coinapi.io/pricing
- Set sidebar refresh to 60s (260 calls/day → ~3h of use per day on free plan)
- Use a paid plan for production deployment
        """)

    st.divider()
    st.markdown("<div style='text-align:center;color:#4a5568;font-size:.8rem'>"
                "⚠️ Paper trading only — no real money. CoinAPI provides real market data."
                "</div>", unsafe_allow_html=True)
