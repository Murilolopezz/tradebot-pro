import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import requests
import smtplib
import threading
import schedule
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import anthropic

load_dotenv()
GMAIL_USER    = os.getenv("GMAIL_USER", "")
GMAIL_PASS    = os.getenv("GMAIL_PASS", "")
NEWS_API_KEY  = os.getenv("NEWS_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
APP_PASSWORD  = os.getenv("APP_PASSWORD", "tradebot2024")
MANUTENCAO    = os.getenv("MANUTENCAO", "false").lower() == "true"
ADMIN_PASS    = os.getenv("ADMIN_PASS", "admin2024")

st.set_page_config(page_title="TradeBot Pro", page_icon="📈", layout="wide")

CSS_BASE = """<style>
html,body,.stApp{background:#080c10!important;}
.login-box{max-width:380px;margin:80px auto;background:#0e1318;border:1px solid #1a2332;border-radius:16px;padding:40px;text-align:center;}
.login-title{font-family:'Syne',sans-serif;font-size:1.9rem;font-weight:800;background:linear-gradient(135deg,#00d4aa,#0ea5e9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px;}
.login-sub{color:#64748b;font-family:Space Mono,monospace;font-size:0.75rem;letter-spacing:1px;margin-bottom:28px;}
</style>"""

# ─── Modo Manutenção ──────────────────────────────────────────────────────────
if MANUTENCAO:
    if "admin_ok" not in st.session_state: st.session_state.admin_ok = False
    if not st.session_state.admin_ok:
        st.markdown(CSS_BASE, unsafe_allow_html=True)
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>🔧 Em Manutenção</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-sub'>VOLTAMOS EM BREVE · TRADEBOT PRO</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b;font-size:0.85rem;margin-bottom:16px;'>Estamos realizando melhorias no sistema.</p>", unsafe_allow_html=True)
        adm = st.text_input("", type="password", placeholder="Acesso admin", label_visibility="collapsed")
        if st.button("🔓 Entrar como Admin", use_container_width=True):
            if adm == ADMIN_PASS:
                st.session_state.admin_ok = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

# ─── Login Gate ───────────────────────────────────────────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown(CSS_BASE, unsafe_allow_html=True)
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<div class='login-title'>📈 TradeBot Pro</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-sub'>ACESSO RESTRITO · INSIRA A SENHA</div>", unsafe_allow_html=True)
    senha_inp = st.text_input("", type="password", placeholder="Digite a senha de acesso", label_visibility="collapsed")
    if st.button("🔓 Entrar", use_container_width=True):
        if senha_inp == APP_PASSWORD:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

def inject_css():
    st.markdown("""<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">""", unsafe_allow_html=True)
    st.markdown("""<style>
:root {
    --bg:      #080c10;
    --surface: #0e1318;
    --border:  #1a2332;
    --accent:  #00d4aa;
    --accent2: #0ea5e9;
    --danger:  #f43f5e;
    --warn:    #f59e0b;
    --text:    #e2e8f0;
    --muted:   #64748b;
    --buy:     #00d4aa;
    --sell:    #f43f5e;
    --neutral: #f59e0b;
}
html, body, .stApp { background-color: var(--bg) !important; color: var(--text); font-family: 'Syne', sans-serif; }
.stApp > header { background: transparent !important; }
section[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }

.stTabs [data-baseweb="tab-list"] {
    background: var(--surface);
    border-radius: 12px;
    padding: 4px 4px 8px 4px;
    border: 1px solid var(--border);
    gap: 2px;
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    scrollbar-color: var(--accent) #1a2332;
    cursor: grab;
    user-select: none;
}
.stTabs [data-baseweb="tab-list"]:active { cursor: grabbing; }
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { height: 4px; }
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-track { background: #1a2332; border-radius: 4px; }
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 4px; }
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb:hover { background: var(--accent2); }
.stTabs [data-baseweb="tab"] { color: var(--muted); font-weight: 600; border-radius: 8px; font-family: 'Syne', sans-serif; font-size: 0.82rem; padding: 6px 12px; white-space: nowrap !important; flex-shrink: 0 !important; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #00d4aa22, #0ea5e922) !important; color: var(--accent) !important; border: 1px solid var(--accent) !important; }

.stTextInput input, .stSelectbox select { background: var(--surface) !important; border: 1px solid var(--border) !important; color: var(--text) !important; border-radius: 8px !important; font-family: 'Space Mono', monospace !important; }
div[data-baseweb="select"] > div { background: var(--surface) !important; border-color: var(--border) !important; }

.stButton > button { background: linear-gradient(135deg, var(--accent), var(--accent2)) !important; color: #000 !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; font-family: 'Syne', sans-serif !important; transition: all 0.2s ease; }
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,212,170,0.3); }

div[data-testid="metric-container"] { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px; transition: border-color 0.2s; }
div[data-testid="metric-container"]:hover { border-color: var(--accent); }
div[data-testid="metric-container"] label { color: var(--muted) !important; font-size: 0.75rem !important; font-family: 'Space Mono', monospace; text-transform: uppercase; letter-spacing: 1px; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-family: 'Space Mono', monospace; font-size: 1.3rem; color: var(--text); }

.stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid var(--border); }
.stProgress > div > div { background: linear-gradient(90deg, var(--accent), var(--accent2)) !important; border-radius: 4px; }

/* FIX: remove white hover on expander */
.streamlit-expanderHeader:hover { background-color: var(--surface) !important; }
details summary:hover { background: var(--surface) !important; }
details { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; }
details[open] { border-color: var(--accent) !important; }

.news-card { background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--accent2); border-radius: 10px; padding: 14px; margin: 6px 0; transition: border-color 0.2s, transform 0.2s; }
.news-card:hover { border-color: var(--accent); transform: translateX(3px); }
.news-urgent { background: linear-gradient(135deg, #f59e0b08, #f59e0b18); border: 1px solid var(--warn) !important; border-left: 4px solid var(--warn) !important; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(245,158,11,0.3)} 50%{box-shadow:0 0 12px 4px rgba(245,158,11,0.15)} }

.signal-buy     { background: linear-gradient(135deg, #00d4aa08, #00d4aa15); border: 1px solid var(--buy);     border-radius: 12px; padding: 16px; }
.signal-sell    { background: linear-gradient(135deg, #f43f5e08, #f43f5e15); border: 1px solid var(--sell);    border-radius: 12px; padding: 16px; }
.signal-neutral { background: linear-gradient(135deg, #f59e0b08, #f59e0b15); border: 1px solid var(--neutral); border-radius: 12px; padding: 16px; }

.ai-card { background: linear-gradient(135deg, #0a1628, #0d1f3c); border: 1px solid #1a3a5c; border-radius: 14px; padding: 20px; margin-top: 12px; position: relative; overflow: hidden; }
.ai-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background: linear-gradient(90deg, var(--accent), var(--accent2), var(--accent)); }
.ai-label { font-family:'Space Mono',monospace; font-size:0.7rem; color:var(--accent); text-transform:uppercase; letter-spacing:2px; margin-bottom:8px; }
.ai-text { color:var(--text); line-height:1.7; font-size:0.92rem; }

.indice-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; transition: border-color 0.2s, transform 0.2s; }
.indice-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.indice-nome { font-family:'Space Mono',monospace; font-size:0.75rem; color:var(--muted); text-transform:uppercase; letter-spacing:1px; }
.indice-valor { font-family:'Space Mono',monospace; font-size:1.4rem; font-weight:700; color:var(--text); margin:4px 0; }
.indice-var-pos { color: var(--buy); font-weight:700; font-family:'Space Mono',monospace; font-size:0.9rem; }
.indice-var-neg { color: var(--sell); font-weight:700; font-family:'Space Mono',monospace; font-size:0.9rem; }

.header-main { font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800; background:linear-gradient(135deg,var(--accent),var(--accent2)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; letter-spacing:-1px; margin-bottom:2px; }
.header-sub { color:var(--muted); font-size:0.85rem; font-family:'Space Mono',monospace; letter-spacing:1px; }

div[data-testid="stAlert"] { border-radius:8px !important; border-left-width:3px !important; }
div.stSlider > div { padding-top:4px; }
</style>""", unsafe_allow_html=True)

inject_css()

# Drag-to-scroll nas abas
st.markdown("""<script>
(function() {
  function enableDrag(el) {
    let isDown = false, startX, scrollLeft;
    el.addEventListener('mousedown', e => {
      isDown = true; el.classList.add('active');
      startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft;
    });
    el.addEventListener('mouseleave', () => { isDown = false; el.classList.remove('active'); });
    el.addEventListener('mouseup',    () => { isDown = false; el.classList.remove('active'); });
    el.addEventListener('mousemove',  e => {
      if (!isDown) return; e.preventDefault();
      const x = e.pageX - el.offsetLeft;
      el.scrollLeft = scrollLeft - (x - startX) * 1.5;
    });
  }
  function init() {
    const tabList = document.querySelector('[data-baseweb="tab-list"]');
    if (tabList) { enableDrag(tabList); }
    else { setTimeout(init, 500); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
</script>""", unsafe_allow_html=True)

# ─── Catálogo ────────────────────────────────────────────────────────────────
CATALOGO = {
    "B3 — Bancos":         ["ITUB4.SA","BBDC4.SA","BBAS3.SA","SANB11.SA","BPAC11.SA","IRBR3.SA","BMGB4.SA","BRSR6.SA","ABCB4.SA"],
    "B3 — Energia":        ["PETR4.SA","PETR3.SA","PRIO3.SA","RECV3.SA","RRRP3.SA","UGPA3.SA","CSAN3.SA","VBBR3.SA","ENGI11.SA","EGIE3.SA","CPFE3.SA","TAEE11.SA","CMIG4.SA","AURE3.SA","CPLE6.SA"],
    "B3 — Mineração":      ["VALE3.SA","CSNA3.SA","GGBR4.SA","USIM5.SA","CMIN3.SA"],
    "B3 — Agro":           ["AGRO3.SA","SLCE3.SA","SMTO3.SA","CAML3.SA","BEEF3.SA","MRFG3.SA","JBSS3.SA","BRFS3.SA"],
    "B3 — Tecnologia":     ["TOTS3.SA","POSI3.SA","LWSA3.SA","CASH3.SA","TIMS3.SA","VIVT3.SA"],
    "B3 — Varejo":         ["MGLU3.SA","LREN3.SA","ARZZ3.SA","ABEV3.SA","SOMA3.SA","PETZ3.SA","VIVA3.SA"],
    "B3 — Saúde":          ["RDOR3.SA","HAPV3.SA","QUAL3.SA","FLRY3.SA","RADL3.SA","DASA3.SA"],
    "B3 — Construção":     ["CYRE3.SA","MRVE3.SA","EVEN3.SA","EZTC3.SA","DIRR3.SA","TEND3.SA"],
    "B3 — Papel/Indústria":["KLBN11.SA","SUZB3.SA","DXCO3.SA","WEGE3.SA","EMBR3.SA"],
    "B3 — Transporte":     ["RENT3.SA","RAIL3.SA","GOLL4.SA","AZUL4.SA","CCRO3.SA","ECOR3.SA"],
    "EUA — Big Tech":      ["AAPL","MSFT","GOOGL","META","AMZN","NVDA","TSLA","ORCL","IBM","INTC","NFLX","ADBE","CRM","QCOM","AMD"],
    "EUA — Mídia/Entret.": ["WBD","PARA","DIS","CMCSA","FOX","FOXA","SIRI","LYV","SPOT","ROKU"],
    "EUA — Finanças":      ["JPM","BAC","WFC","GS","MS","C","AXP","BLK","V","MA","SCHW","COF"],
    "EUA — Saúde":         ["JNJ","PFE","MRK","ABBV","UNH","CVS","LLY","BMY","AMGN","GILD"],
    "EUA — Energia":       ["XOM","CVX","COP","SLB","EOG","MPC","PSX","OXY","HAL","DVN"],
    "EUA — Consumo":       ["WMT","COST","TGT","HD","MCD","SBUX","NKE","LOW","AMZN","BABA"],
    "Cripto":              ["BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD","ADA-USD","DOGE-USD","AVAX-USD","DOT-USD","MATIC-USD","LINK-USD","LTC-USD","ATOM-USD","UNI7083-USD","NEAR-USD"],
    "FIIs":                ["HGLG11.SA","XPML11.SA","VISC11.SA","KNRI11.SA","MXRF11.SA","BCFF11.SA","XPLG11.SA","MALL11.SA","BRCR11.SA","RBRF11.SA","BTLG11.SA","GGRC11.SA"],
    "ETFs BR":             ["BOVA11.SA","SMAL11.SA","IVVB11.SA","HASH11.SA","GOLD11.SA","DIVO11.SA","AGRI11.SA","SPXI11.SA"],
    "ETFs EUA":            ["SPY","QQQ","IWM","DIA","VTI","GLD","SLV","TLT","XLK","XLF","XLE","ARKK"],
}

INDICES = [
    ("Ibovespa",  "^BVSP",  "BR"),
    ("S&P 500",   "^GSPC",  "EUA"),
    ("Nasdaq",    "^IXIC",  "EUA"),
    ("Dow Jones", "^DJI",   "EUA"),
    ("DAX",       "^GDAXI", "EU"),
    ("FTSE 100",  "^FTSE",  "EU"),
    ("Nikkei",    "^N225",  "ASIA"),
    ("Hang Seng", "^HSI",   "ASIA"),
    ("Ouro",      "GC=F",   "Comod."),
    ("Petróleo",  "CL=F",   "Comod."),
    ("Dólar/BRL", "USDBRL=X","FX"),
    ("Bitcoin",   "BTC-USD", "Cripto"),
]

FUNDOS = [
    ("Butiá Excellence FIC", "Renda Fixa", "~13.5% a.a.", "Baixo", "AAA"),
    ("BTG Pactual Tesouro Selic", "Renda Fixa", "~14.5% a.a.", "Baixo", "AAA"),
    ("Verde AM", "Multimercado", "CDI+5%~8%", "Médio", "A+"),
    ("SPX Nimitz", "Multimercado", "CDI+6%~10%", "Médio-Alto", "A+"),
    ("Kinea Prev XP", "Previdência", "CDI+4%", "Médio", "AA"),
    ("ARX Income", "Renda Fixa", "CDI+1.5%", "Baixo", "AA"),
    ("Kapitalo Kappa", "Multimercado", "CDI+7%", "Alto", "A"),
    ("Ibiuna Hedge", "Multimercado", "CDI+5%", "Médio", "A+"),
    ("XP Long Biased", "Renda Variável", "IBOV+5%", "Alto", "A"),
    ("BTG Absoluto", "Multimercado", "CDI+8%", "Alto", "A"),
]

# ─── Session State ────────────────────────────────────────────────────────────
if "alertas_preco"     not in st.session_state: st.session_state.alertas_preco = []
if "alertas_disparados" not in st.session_state: st.session_state.alertas_disparados = []
if "sched"             not in st.session_state: st.session_state.sched = False
if "noticias_urgentes" not in st.session_state: st.session_state.noticias_urgentes = []

# ─── Indicadores ─────────────────────────────────────────────────────────────
def calcular_indicadores(df):
    df = df.copy()
    df["SMA20"]   = df["Close"].rolling(20).mean()
    df["SMA50"]   = df["Close"].rolling(50).mean()
    df["SMA200"]  = df["Close"].rolling(200).mean()
    df["EMA9"]    = df["Close"].ewm(span=9,  adjust=False).mean()
    df["EMA21"]   = df["Close"].ewm(span=21, adjust=False).mean()
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + gain / loss))
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]   = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["Hist"]   = df["MACD"] - df["Signal"]
    tr = pd.concat([df["High"]-df["Low"],(df["High"]-df["Close"].shift()).abs(),(df["Low"]-df["Close"].shift()).abs()],axis=1).max(axis=1)
    df["ATR"]      = tr.rolling(14).mean()
    df["BB_mid"]   = df["Close"].rolling(20).mean()
    std            = df["Close"].rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2*std
    df["BB_lower"] = df["BB_mid"] - 2*std
    df["Vol_media"]= df["Volume"].rolling(20).mean()
    return df

def gerar_analise(df, ticker):
    ultimo = df["Close"].iloc[-1]
    sma20  = df["SMA20"].iloc[-1]
    sma50  = df["SMA50"].iloc[-1]
    rsi    = df["RSI"].iloc[-1]
    macd   = df["MACD"].iloc[-1]
    signal = df["Signal"].iloc[-1]
    atr    = df["ATR"].iloc[-1]
    bb_up  = df["BB_upper"].iloc[-1]
    bb_low = df["BB_lower"].iloc[-1]
    vol_at = df["Volume"].iloc[-1]
    vol_md = df["Vol_media"].iloc[-1]
    var    = ((ultimo - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100
    var1d  = ((ultimo - df["Close"].iloc[-2]) / df["Close"].iloc[-2]) * 100 if len(df)>1 else 0
    score = 50; pros, contras, alertas = [], [], []
    if ultimo > sma20: score+=8;  pros.append("📈 Preço acima da SMA20 — momentum positivo")
    else:              score-=8;  contras.append("📉 Preço abaixo da SMA20 — pressão vendedora")
    if ultimo > sma50: score+=10; pros.append("✅ Acima da SMA50 — tendência intermediária de alta")
    else:              score-=10; contras.append("⚠️ Abaixo da SMA50 — tendência intermediária de baixa")
    sma200 = df["SMA200"].iloc[-1]
    if not pd.isna(sma200):
        if ultimo > sma200: score+=12; pros.append("🏆 Acima da SMA200 — bull market de longo prazo")
        else:               score-=12; contras.append("🐻 Abaixo da SMA200 — bear market de longo prazo")
    if rsi < 30:   score+=18; pros.append(f"🟢 RSI {rsi:.1f} — SOBREVENDA! Possível reversão"); alertas.append("🔔 RSI em sobrevenda — oportunidade!")
    elif rsi < 45: score+=8;  pros.append(f"📊 RSI {rsi:.1f} — fraqueza, possível recuperação")
    elif rsi > 70: score-=15; contras.append(f"🔴 RSI {rsi:.1f} — SOBRECOMPRA! Risco de correção"); alertas.append("⚠️ RSI em sobrecompra — cuidado!")
    elif rsi > 60: score+=5;  pros.append(f"📊 RSI {rsi:.1f} — força moderada")
    else:          score+=3;  pros.append(f"📊 RSI {rsi:.1f} — zona neutra")
    macd_prev = df["MACD"].iloc[-2]; sig_prev = df["Signal"].iloc[-2]
    if macd>signal and macd_prev<=sig_prev:   score+=15; pros.append("🚀 Cruzamento MACD para cima — sinal de COMPRA!"); alertas.append("🔔 Cruzamento de alta no MACD!")
    elif macd>signal:                          score+=8;  pros.append("✅ MACD positivo — momentum favorável")
    elif macd<signal and macd_prev>=sig_prev:  score-=15; contras.append("💀 Cruzamento MACD para baixo — sinal de VENDA!"); alertas.append("⚠️ Cruzamento de baixa no MACD!")
    else:                                      score-=8;  contras.append("❌ MACD negativo — momentum desfavorável")
    if ultimo <= bb_low: score+=10; pros.append("🎯 Na banda inferior de Bollinger — suporte/reversão")
    elif ultimo >= bb_up: score-=10; contras.append("⚡ Na banda superior de Bollinger — sobreextensão")
    if not pd.isna(vol_md) and vol_md>0:
        vr = vol_at/vol_md
        if vr>2:     score+=8; pros.append(f"📊 Volume {vr:.1f}x acima da média — forte interesse")
        elif vr<0.5: score-=5; contras.append("😴 Volume abaixo da média")
    if var>0: score+=5; pros.append(f"📈 +{var:.1f}% no período")
    else:     score-=5; contras.append(f"📉 {var:.1f}% no período")
    score = max(0, min(100, score))
    if score>=75:   rec="🟢 FORTE COMPRA"
    elif score>=60: rec="🟩 COMPRA"
    elif score>=45: rec="🟡 NEUTRO"
    elif score>=30: rec="🟠 VENDA PARCIAL"
    else:           rec="🔴 VENDA / EVITAR"
    alvo_a = round(ultimo*(1+(atr/ultimo)*3),2) if not pd.isna(atr) else None
    alvo_b = round(ultimo*(1-(atr/ultimo)*2),2) if not pd.isna(atr) else None
    return score, pros, contras, alertas, rec, var, var1d, alvo_a, alvo_b

def analisar_com_claude(ticker, df, info, score, pros, contras, rec, var, var1d, alvo_a, alvo_b):
    if not ANTHROPIC_KEY: return None, "Configure ANTHROPIC_API_KEY no .env."
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        preco  = df["Close"].iloc[-1]
        rsi    = df["RSI"].iloc[-1]
        macd   = df["MACD"].iloc[-1]
        signal = df["Signal"].iloc[-1]
        atr    = df["ATR"].iloc[-1]
        nome   = info.get("longName", ticker) if info else ticker
        setor  = info.get("sector", "N/A") if info else "N/A"
        prompt = f"""Você é um analista financeiro especialista em mercados Brasil e EUA.
Analise o ativo {ticker} ({nome}) — Setor: {setor}

DADOS TÉCNICOS:
- Preço atual: {preco:.2f} | Var. período: {var:+.2f}% | Var. 1d: {var1d:+.2f}%
- RSI (14): {rsi:.1f} | MACD: {macd:.4f} | Sinal: {signal:.4f} | ATR: {atr:.2f}
- Score interno: {score}/100 | Recomendação: {rec}
- Alvo: {alvo_a} | Stop: {alvo_b}

FATORES POSITIVOS: {', '.join(pros[:4])}
FATORES NEGATIVOS: {', '.join(contras[:4])}

Forneça análise em português com exatamente estas 4 seções:

## 1. Contexto Macro
[2-3 linhas sobre o setor/ativo no cenário atual]

## 2. Análise Técnica Detalhada
[3-4 linhas interpretando os indicadores]

## 3. Estratégia de Trade
[Entrada, alvo, stop-loss, relação risco/retorno, perfil de investidor adequado]

## 4. Risco Principal
[1-2 linhas sobre o principal risco a monitorar]

Seja direto e objetivo. Máximo 280 palavras."""
        msg = client.messages.create(model="claude-opus-4-6", max_tokens=700,
            messages=[{"role":"user","content":prompt}])
        return msg.content[0].text, None
    except Exception as e:
        return None, f"Erro IA: {str(e)}"

def buscar_noticias(query, n=8, lang="pt"):
    if not NEWS_API_KEY: return []
    try:
        r = requests.get(f"https://newsapi.org/v2/everything?q={query}&language={lang}&sortBy=publishedAt&pageSize={n}&apiKey={NEWS_API_KEY}", timeout=8)
        arts = r.json().get("articles", [])
        if not arts and lang=="pt":
            r2 = requests.get(f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize={n}&apiKey={NEWS_API_KEY}", timeout=8)
            arts = r2.json().get("articles", [])
        return [a for a in arts if a.get("title") and a.get("title") != "[Removed]"]
    except: return []

def buscar_noticias_multi(queries, n_cada=5):
    """Busca notícias de múltiplas queries e deduplica"""
    vistas = set(); resultado = []
    for q, lang in queries:
        arts = buscar_noticias(q, n=n_cada, lang=lang)
        for a in arts:
            titulo = a.get("title","")
            if titulo not in vistas:
                vistas.add(titulo)
                resultado.append(a)
    resultado.sort(key=lambda x: x.get("publishedAt",""), reverse=True)
    return resultado

def plotar_grafico(df, ticker):
    # FIX: usar índice numérico para evitar problemas com timezone no eixo X
    datas = [str(d)[:10] for d in df.index]
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.55,0.15,0.15,0.15],
        subplot_titles=(f"{ticker}","Volume","RSI (14)","MACD"))
    x = list(range(len(df)))
    fig.add_trace(go.Candlestick(x=datas, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Preço",
        increasing_line_color="#00d4aa", decreasing_line_color="#f43f5e",
        increasing_fillcolor="#00d4aa", decreasing_fillcolor="#f43f5e"), row=1, col=1)
    for col, color, dash in [("SMA20","#FFD700","solid"),("SMA50","#FF8C00","solid"),
        ("SMA200","#f43f5e","dash"),("EMA9","#00d4aa","dot"),("EMA21","#0ea5e9","dot")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=datas, y=df[col], name=col,
                line=dict(color=color, width=1.3, dash=dash), opacity=0.85), row=1, col=1)
    fig.add_trace(go.Scatter(x=datas, y=df["BB_upper"], name="BB+",
        line=dict(color="#7c3aed",width=1,dash="dash"),opacity=0.5), row=1, col=1)
    fig.add_trace(go.Scatter(x=datas, y=df["BB_lower"], name="BB-",
        line=dict(color="#7c3aed",width=1,dash="dash"),
        fill="tonexty", fillcolor="rgba(124,58,237,0.04)", opacity=0.5), row=1, col=1)
    cores_vol = ["#00d4aa" if c>=o else "#f43f5e" for c,o in zip(df["Close"],df["Open"])]
    fig.add_trace(go.Bar(x=datas, y=df["Volume"], name="Volume", marker_color=cores_vol, opacity=0.7), row=2, col=1)
    if "Vol_media" in df.columns:
        fig.add_trace(go.Scatter(x=datas, y=df["Vol_media"], name="Vol Med",
            line=dict(color="#f59e0b",width=1.2,dash="dot")), row=2, col=1)
    fig.add_trace(go.Scatter(x=datas, y=df["RSI"], name="RSI",
        line=dict(color="#a78bfa",width=1.8)), row=3, col=1)
    fig.add_hrect(y0=70,y1=100,fillcolor="rgba(244,63,94,0.07)",line_width=0,row=3,col=1)
    fig.add_hrect(y0=0,y1=30,fillcolor="rgba(0,212,170,0.07)",line_width=0,row=3,col=1)
    fig.add_hline(y=70,line_dash="dash",line_color="#f43f5e",opacity=0.5,row=3,col=1)
    fig.add_hline(y=30,line_dash="dash",line_color="#00d4aa",opacity=0.5,row=3,col=1)
    fig.add_hline(y=50,line_dash="dot",line_color="#64748b",opacity=0.4,row=3,col=1)
    cores_hist = ["#00d4aa" if v>=0 else "#f43f5e" for v in df["Hist"]]
    fig.add_trace(go.Bar(x=datas, y=df["Hist"], name="Hist", marker_color=cores_hist, opacity=0.7), row=4, col=1)
    fig.add_trace(go.Scatter(x=datas, y=df["MACD"], name="MACD", line=dict(color="#0ea5e9",width=1.8)), row=4, col=1)
    fig.add_trace(go.Scatter(x=datas, y=df["Signal"], name="Sinal", line=dict(color="#f59e0b",width=1.8)), row=4, col=1)
    fig.update_layout(template="plotly_dark", height=900, paper_bgcolor="#080c10", plot_bgcolor="#080c10",
        xaxis_rangeslider_visible=False, showlegend=True,
        legend=dict(orientation="h",x=0,y=1.08,font=dict(size=9,color="#64748b"),bgcolor="rgba(0,0,0,0)",itemwidth=40),
        margin=dict(l=60,r=20,t=80,b=20), font=dict(color="#e2e8f0"))
    for i in range(1,5):
        fig.update_xaxes(gridcolor="#1a2332",showgrid=True,row=i,col=1,showticklabels=(i==4))
        fig.update_yaxes(gridcolor="#1a2332",showgrid=True,row=i,col=1)
    fig.update_xaxes(showticklabels=True,row=4,col=1)
    fig.update_yaxes(title_text="Preço",row=1,col=1,title_font=dict(size=10))
    fig.update_yaxes(title_text="Vol",  row=2,col=1,title_font=dict(size=10))
    fig.update_yaxes(title_text="RSI",  row=3,col=1,range=[0,100],title_font=dict(size=10))
    fig.update_yaxes(title_text="MACD", row=4,col=1,title_font=dict(size=10))
    for trace in fig.data:
        if trace.name in ["RSI","Hist","Sinal","Vol Med","Volume"]: trace.showlegend = False
    return fig

def buscar_ativo(ticker, periodo):
    try:
        d = yf.Ticker(ticker)
        h = d.history(period=periodo)
        if h.empty or len(h)<30: return None, None
        h.index = h.index.tz_localize(None) if h.index.tz is not None else h.index
        return calcular_indicadores(h), d.info
    except: return None, None

def enviar_email(assunto, corpo):
    if not GMAIL_USER or not GMAIL_PASS: return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"]=assunto; msg["From"]=GMAIL_USER; msg["To"]=GMAIL_USER
        msg.attach(MIMEText(corpo,"html"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(GMAIL_USER,GMAIL_PASS)
            s.sendmail(GMAIL_USER,GMAIL_USER,msg.as_string())
        return True
    except: return False

def gerar_newsletter():
    amostra = ["PETR4.SA","VALE3.SA","ITUB4.SA","WEGE3.SA","PRIO3.SA","KLBN11.SA","AAPL","NVDA","MSFT","BTC-USD","ETH-USD","BBAS3.SA"]
    compras, vendas = [], []
    for tk in amostra:
        df,_ = buscar_ativo(tk,"1mo")
        if df is not None:
            score,_,_,alertas,rec,var,_,_,_ = gerar_analise(df,tk)
            entry = (tk,score,rec,var,alertas)
            if "COMPRA" in rec: compras.append(entry)
            elif "VENDA" in rec or score < 40: vendas.append(entry)
    compras.sort(key=lambda x:x[1],reverse=True)
    vendas.sort(key=lambda x:x[1])

    def bloco_ativo(tk,score,rec,var,alertas):
        cor = "#00d4aa" if "COMPRA" in rec else "#f43f5e"
        return f"""<div style="background:#0e1318;border:1px solid #1a2332;border-left:4px solid {cor};border-radius:10px;padding:14px;margin:8px 0;">
<b style="color:#0ea5e9;font-size:1.05rem;">{tk}</b>
<span style="background:{cor};color:#000;padding:2px 10px;border-radius:20px;margin-left:8px;font-weight:700;font-size:0.82rem;">{rec}</span>
<br><span style="color:#64748b;font-size:0.85rem;">Score: {score}/100 &nbsp;|&nbsp; Var: {var:+.1f}%</span>
{"".join(f"<br><span style=\"color:#f59e0b;font-size:0.82rem;\">⚡ {a}</span>" for a in alertas)}
</div>"""

    # Mensagem do dia via Claude
    msg_dia = ""
    if ANTHROPIC_KEY:
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            r = client.messages.create(model="claude-opus-4-6", max_tokens=200,
                messages=[{"role":"user","content":f"Escreva uma mensagem motivacional e inteligente de 2-3 frases para investidores para o dia {datetime.now().strftime('%d/%m/%Y')}. Mencione algo relevante sobre o mercado financeiro atual. Seja inspirador mas realista."}])
            msg_dia = r.content[0].text
        except: msg_dia = "O mercado recompensa quem estuda, planeja e mantém a disciplina. Bons trades hoje!"

    # Notícias por região
    nots_br = buscar_noticias("bolsa B3 Ibovespa Brasil mercado", n=4)
    nots_us = buscar_noticias("stock market NYSE Nasdaq Fed", n=4, lang="en")
    nots_global = buscar_noticias("global economy geopolitics trade war", n=3, lang="en")

    def bloco_noticias(noticias, titulo, cor):
        html = f"<h3 style='color:{cor};margin-top:20px;'>{titulo}</h3>"
        for n in noticias:
            url = n.get("url","#"); t = n.get("title",""); fonte = n.get("source",{}).get("name",""); data = n.get("publishedAt","")[:10]
            html += f"""<div style="background:#0e1318;border-left:3px solid {cor};padding:10px 14px;margin:6px 0;border-radius:6px;">
<a href="{url}" style="color:#e2e8f0;text-decoration:none;font-weight:600;font-size:0.92rem;">{t}</a>
<br><span style="color:#64748b;font-size:0.78rem;">{fonte} — {data}</span>
</div>"""
        return html

    corpo = f"""<html><body style="background:#080c10;color:#e2e8f0;font-family:Arial,sans-serif;padding:24px;max-width:700px;margin:auto;">
<h1 style="color:#00d4aa;border-bottom:2px solid #1a2332;padding-bottom:12px;">📈 TradeBot Pro — Newsletter</h1>
<p style="color:#64748b;font-family:monospace;">{datetime.now().strftime("%d/%m/%Y %H:%M")}</p>

<div style="background:linear-gradient(135deg,#0a1628,#0d1f3c);border:1px solid #1a3a5c;border-radius:12px;padding:18px;margin:16px 0;">
<div style="color:#00d4aa;font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">💡 Mensagem do Dia</div>
<p style="color:#e2e8f0;line-height:1.7;margin:0;">{msg_dia}</p>
</div>

<h2 style="color:#00d4aa;">🟢 Oportunidades de Compra</h2>
{"".join(bloco_ativo(*c) for c in compras[:5]) if compras else "<p style='color:#64748b;'>Nenhuma oportunidade de compra identificada hoje.</p>"}

<h2 style="color:#f43f5e;">🔴 Sinais de Venda / Cautela</h2>
{"".join(bloco_ativo(*v) for v in vendas[:4]) if vendas else "<p style='color:#64748b;'>Nenhum sinal de venda identificado hoje.</p>"}

<hr style="border-color:#1a2332;margin:24px 0;">
{bloco_noticias(nots_br,"🇧🇷 Mercado Brasileiro","#00d4aa")}
{bloco_noticias(nots_us,"🇺🇸 Mercado Americano","#0ea5e9")}
{bloco_noticias(nots_global,"🌍 Geopolítica & Mundo","#f59e0b")}

<p style="color:#64748b;font-size:0.75rem;margin-top:24px;text-align:center;">TradeBot Pro · Este email é informativo e não constitui recomendação de investimento.</p>
</body></html>"""
    return enviar_email(f"📈 TradeBot Pro — {datetime.now().strftime('%d/%m')} · Oportunidades do Dia", corpo)

def verificar_alertas():
    for alerta in st.session_state.alertas_preco:
        if not alerta.get("ativo", True): continue
        try:
            tk = yf.Ticker(alerta["ticker"])
            hist = tk.history(period="1d", interval="5m")
            if hist.empty: continue
            preco_atual = hist["Close"].iloc[-1]
            disparar = (alerta["tipo"]=="acima" and preco_atual>=alerta["valor"]) or \
                       (alerta["tipo"]=="abaixo" and preco_atual<=alerta["valor"])
            if disparar:
                alerta["ativo"] = False
                st.session_state.alertas_disparados.append({**alerta,"preco_disparado":preco_atual,"hora":datetime.now().strftime("%d/%m %H:%M")})
                enviar_email(f"🔔 Alerta: {alerta['ticker']}",
                    f"<h2>Alerta disparado!</h2><p>{alerta['ticker']} atingiu {preco_atual:.2f}</p>")
        except: pass

def rodar_scheduler():
    schedule.every().day.at("07:00").do(gerar_newsletter)
    schedule.every().day.at("13:00").do(gerar_newsletter)
    schedule.every().day.at("18:00").do(gerar_newsletter)
    schedule.every(5).minutes.do(verificar_alertas)
    while True: schedule.run_pending(); time.sleep(60)

if not st.session_state.sched:
    st.session_state.sched = True
    threading.Thread(target=rodar_scheduler, daemon=True).start()

def render_noticias(lista, max_desc=220):
    """Renderiza cards de notícias com links clicáveis e descrição completa"""
    for n in lista:
        titulo = n.get("title",""); fonte = n.get("source",{}).get("name","")
        data   = n.get("publishedAt","")[:10]; desc = n.get("description","") or ""
        url_n  = n.get("url","#")
        urgente = any(p in titulo.lower() for p in ["urgente","breaking","alerta","crash","colapso","guerra","ataque","sanção"])
        classe = "news-card news-urgent" if urgente else "news-card"
        badge  = "<span style='background:#f59e0b;color:#000;font-size:0.65rem;padding:2px 6px;border-radius:4px;font-weight:700;margin-right:6px;'>🔴 URGENTE</span>" if urgente else ""
        st.markdown(f"""<div class='{classe}'>
{badge}<b><a href='{url_n}' target='_blank' style='color:#0ea5e9;text-decoration:none;font-size:0.95rem;'>{titulo}</a></b>
<br><span style='color:#64748b;font-size:0.78rem;'>📰 {fonte} · {data}</span>
<br><span style='color:#94a3b8;font-size:0.85rem;line-height:1.5;'>{desc[:max_desc]}{"..." if len(desc)>max_desc else ""}</span>
<br><a href='{url_n}' target='_blank' style='color:#00d4aa;font-size:0.78rem;text-decoration:none;'>→ Ler notícia completa</a>
</div>""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#00d4aa;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;'>TradeBot Pro v3</div>", unsafe_allow_html=True)
    if st.session_state.alertas_disparados:
        st.markdown(f"<div style='background:#f59e0b15;border:1px solid #f59e0b;border-radius:8px;padding:10px;margin-bottom:12px;'><b style='color:#f59e0b;'>🔔 {len(st.session_state.alertas_disparados)} alerta(s) disparado(s)!</b></div>", unsafe_allow_html=True)
        for ad in st.session_state.alertas_disparados[-3:]:
            st.markdown(f"<div style='font-size:0.78rem;color:#f59e0b;font-family:Space Mono,monospace;'>{ad['ticker']} {ad['tipo']} {ad['valor']:.2f} → {ad['preco_disparado']:.2f} [{ad['hora']}]</div>", unsafe_allow_html=True)
        if st.button("Limpar alertas"):
            st.session_state.alertas_disparados = []
            st.rerun()
    st.markdown("---")
    st.markdown("<div style='font-size:0.75rem;color:#64748b;font-family:Space Mono,monospace;'>⚙️ Status das APIs</div>", unsafe_allow_html=True)
    for nome_api, val in [("Claude IA", ANTHROPIC_KEY), ("Gmail", GMAIL_USER), ("NewsAPI", NEWS_API_KEY)]:
        cor = "#00d4aa" if val else "#f43f5e"
        st.markdown(f"<div style='font-size:0.75rem;font-family:Space Mono,monospace;color:{cor};'>{nome_api}: {'✅ OK' if val else '❌ Não config.'}</div>", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("<div class='header-main'>📈 TradeBot Pro</div>", unsafe_allow_html=True)
st.markdown("<div class='header-sub'>PLATAFORMA DE ANÁLISE DE MERCADO · POWERED BY CLAUDE AI · V3</div>", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom:20px'></div>", unsafe_allow_html=True)

abas = st.tabs(["🔍 Análise","📡 Screener","🔔 Alertas","📊 Índices","🌍 Mundo","🔥 Hot News","🇧🇷 B3","🇺🇸 EUA","₿ Cripto","🏢 FIIs","📊 ETFs","💼 Fundos","💰 Renda Fixa","📧 Newsletter"])

# ═══════════════════════════════════════════════════════════════════
# ABA 0 — ANÁLISE INDIVIDUAL
# ═══════════════════════════════════════════════════════════════════
with abas[0]:
    st.markdown("### 🔍 Análise Individual")
    c1,c2,c3,c4 = st.columns([3,1,1,1])
    with c1: ticker_inp = st.text_input("Ticker:", value="PETR4.SA", label_visibility="collapsed", placeholder="Ex: PETR4.SA | AAPL | BTC-USD | WBD")
    with c2: periodo_inp = st.selectbox("Período",["1mo","3mo","6mo","1y","2y"],index=2,label_visibility="collapsed")
    with c3: usar_ia = st.checkbox("🤖 IA", value=True)
    with c4:
        st.write("")
        btn = st.button("🔎 Analisar", use_container_width=True)

    if btn:
        with st.spinner(f"Analisando {ticker_inp.upper()}..."):
            df, info = buscar_ativo(ticker_inp.upper(), periodo_inp)
        if df is None:
            st.error("❌ Ativo não encontrado ou dados insuficientes.")
        else:
            score,pros,contras,alertas,rec,var,var1d,alvo_a,alvo_b = gerar_analise(df, ticker_inp.upper())
            for a in alertas: st.warning(a)
            nome  = info.get("longName",  ticker_inp) if info else ticker_inp
            setor = info.get("sector", "") if info else ""
            st.markdown(f"#### {nome} {'— '+setor if setor else ''}")
            m = st.columns(6)
            preco = df["Close"].iloc[-1]
            m[0].metric("Preço",    f"${preco:.2f}",  f"{var1d:+.2f}%")
            m[1].metric("Variação", f"{var:+.2f}%")
            m[2].metric("Máxima",   f"${df['High'].max():.2f}")
            m[3].metric("Mínima",   f"${df['Low'].min():.2f}")
            m[4].metric("RSI",      f"{df['RSI'].iloc[-1]:.1f}")
            m[5].metric("Score",    f"{score}/100")
            st.plotly_chart(plotar_grafico(df, ticker_inp.upper()), use_container_width=True)

            cor_css = "signal-buy" if "COMPRA" in rec else ("signal-sell" if "VENDA" in rec else "signal-neutral")
            cl, cr = st.columns(2)
            with cl:
                alvo_txt = f"<p>🎯 Alvo: <b style='color:#00d4aa'>${alvo_a}</b></p>" if alvo_a else ""
                stop_txt = f"<p>🛡️ Stop: <b style='color:#f43f5e'>${alvo_b}</b></p>" if alvo_b else ""
                st.markdown(f"<div class='{cor_css}'><h3 style='margin:0'>{rec}</h3><p style='color:#64748b;'>Score: <b style='color:white'>{score}/100</b></p>{alvo_txt}{stop_txt}</div>", unsafe_allow_html=True)
            with cr:
                t1,t2 = st.tabs(["✅ Prós","❌ Contras"])
                with t1:
                    for p in pros: st.write(p)
                with t2:
                    for c_ in contras: st.write(c_)

            if usar_ia:
                st.markdown("---")
                st.markdown("#### 🤖 Análise por IA — Claude")
                if not ANTHROPIC_KEY:
                    st.info("Configure `ANTHROPIC_API_KEY` no `.env`.")
                else:
                    with st.spinner("Claude analisando..."):
                        analise_ia, erro_ia = analisar_com_claude(ticker_inp.upper(), df, info, score, pros, contras, rec, var, var1d, alvo_a, alvo_b)
                    if erro_ia: st.error(erro_ia)
                    else:
                        st.markdown(f"""<div class='ai-card'><div class='ai-label'>⚡ Claude AI · Análise Fundamentada</div>
<div class='ai-text'>{analise_ia.replace(chr(10),'<br>')}</div></div>""", unsafe_allow_html=True)

            # Alerta rápido — usa form para evitar reset
            st.markdown("---")
            st.markdown("#### 🔔 Criar Alerta de Preço")
            with st.form(key=f"form_alerta_anal_{ticker_inp}"):
                fa1,fa2,fa3 = st.columns([1,1,1])
                with fa1: tipo_al = st.selectbox("Condição",["acima","abaixo"])
                with fa2: valor_al = st.number_input("Preço alvo:", value=round(preco*1.05,2), step=0.01)
                with fa3:
                    st.write("")
                    submitted = st.form_submit_button("🔔 Criar Alerta", use_container_width=True)
                if submitted:
                    st.session_state.alertas_preco.append({"ticker":ticker_inp.upper(),"tipo":tipo_al,"valor":valor_al,"ativo":True,"criado":datetime.now().strftime("%d/%m %H:%M")})
                    st.success(f"✅ Alerta criado: {ticker_inp.upper()} {tipo_al} {valor_al:.2f}")

            st.markdown("---")
            st.markdown("#### 📰 Notícias Recentes")
            tk_limpo = ticker_inp.replace(".SA","").replace("-USD","")
            noticias = buscar_noticias(f"{tk_limpo} {nome[:25]}", n=8)
            if noticias: render_noticias(noticias)
            else: st.info("Configure NEWS_API_KEY no .env para ver notícias.")

# ═══════════════════════════════════════════════════════════════════
# ABA 1 — SCREENER
# ═══════════════════════════════════════════════════════════════════
with abas[1]:
    st.markdown("### 📡 Screener Automático")
    sc1,sc2,sc3,sc4 = st.columns([2,1,1,1])
    with sc1: cats_sel = st.multiselect("Categorias:", list(CATALOGO.keys()), default=["B3 — Energia","B3 — Bancos","Cripto"])
    with sc2: periodo_sc = st.selectbox("Período:",["1mo","3mo","6mo"],key="sc_p")
    with sc3: min_score = st.slider("Score mín.:",0,100,60)
    with sc4: usar_ia_sc = st.checkbox("🤖 IA", value=False, help="Análise IA nas melhores oportunidades (mais lento)")

    if st.button("🚀 Iniciar Varredura", use_container_width=True):
        tks = list(dict.fromkeys([t for c in cats_sel for t in CATALOGO.get(c,[])]))
        res = []
        bar = st.progress(0)
        for i,tk in enumerate(tks):
            bar.progress((i+1)/len(tks), text=f"Analisando {tk}...")
            df,info = buscar_ativo(tk, periodo_sc)
            if df is not None:
                score,pros,contras,alertas,rec,var,var1d,alvo_a,alvo_b = gerar_analise(df,tk)
                if score>=min_score:
                    res.append({"Ticker":tk,"Preço":round(df["Close"].iloc[-1],2),"Var%":round(var,2),"Var1D%":round(var1d,2),"RSI":round(df["RSI"].iloc[-1],1),"Score":score,"Recomendação":rec,"Alertas":len(alertas),"_df":df,"_info":info,"_pros":pros,"_contras":contras,"_alvo_a":alvo_a,"_alvo_b":alvo_b})
        bar.empty()
        if res:
            res_sorted = sorted(res, key=lambda x:x["Score"], reverse=True)
            df_show = pd.DataFrame([{k:v for k,v in r.items() if not k.startswith("_")} for r in res_sorted])
            st.success(f"✅ {len(df_show)} ativos com score ≥ {min_score}")
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            compras = [r for r in res_sorted if "COMPRA" in r["Recomendação"]]
            if compras:
                st.markdown("### 🟢 Melhores Oportunidades")
                for row in compras[:5]:
                    with st.expander(f"📊 {row['Ticker']} — Score {row['Score']}/100 — {row['Recomendação']}"):
                        g1,g2 = st.columns([3,1])
                        with g1:
                            st.plotly_chart(plotar_grafico(row["_df"], row["Ticker"]), use_container_width=True)
                        with g2:
                            cor = "#00d4aa" if "COMPRA" in row["Recomendação"] else "#f43f5e"
                            st.markdown(f"<div style='background:{cor}15;border:1px solid {cor};border-radius:8px;padding:12px;'><b style='color:{cor};'>{row['Recomendação']}</b><br><span style='color:#64748b;'>Score: {row['Score']}/100</span></div>", unsafe_allow_html=True)
                            st.markdown(f"**RSI:** {row['RSI']}")
                            if row["_alvo_a"]: st.markdown(f"🎯 **Alvo:** ${row['_alvo_a']}")
                            if row["_alvo_b"]: st.markdown(f"🛡️ **Stop:** ${row['_alvo_b']}")
                            # Alerta via form
                            with st.form(key=f"form_sc_{row['Ticker']}"):
                                val_al = st.number_input("Alvo alerta:", value=round(row["Preço"]*1.05,2), step=0.01)
                                if st.form_submit_button("🔔 Criar Alerta"):
                                    st.session_state.alertas_preco.append({"ticker":row["Ticker"],"tipo":"acima","valor":val_al,"ativo":True,"criado":datetime.now().strftime("%d/%m %H:%M")})
                                    st.success("✅")
                            tp,tc = st.tabs(["✅","❌"])
                            with tp:
                                for p in row["_pros"]: st.write(p)
                            with tc:
                                for c_ in row["_contras"]: st.write(c_)
                        # IA no Screener
                        if usar_ia_sc and ANTHROPIC_KEY:
                            st.markdown("---")
                            st.markdown("#### 🤖 Análise IA")
                            with st.spinner("Claude analisando..."):
                                ai_txt, ai_err = analisar_com_claude(row["Ticker"], row["_df"], row["_info"], row["Score"], row["_pros"], row["_contras"], row["Recomendação"], row["Var%"], row["Var1D%"], row["_alvo_a"], row["_alvo_b"])
                            if ai_err: st.error(ai_err)
                            else: st.markdown(f"<div class='ai-card'><div class='ai-label'>⚡ Claude AI</div><div class='ai-text'>{ai_txt.replace(chr(10),'<br>')}</div></div>", unsafe_allow_html=True)
        else:
            st.warning("Nenhum ativo atingiu o score mínimo.")

# ═══════════════════════════════════════════════════════════════════
# ABA 2 — ALERTAS
# ═══════════════════════════════════════════════════════════════════
with abas[2]:
    st.markdown("### 🔔 Alertas de Preço")
    st.markdown("<p style='color:#64748b;font-family:Space Mono,monospace;font-size:0.82rem;'>Verificação a cada 5 minutos · Notificação por e-mail ao disparar</p>", unsafe_allow_html=True)

    with st.form("form_novo_alerta"):
        st.markdown("#### ➕ Novo Alerta")
        fa1,fa2,fa3 = st.columns([2,1,1])
        with fa1: al_ticker = st.text_input("Ticker:", placeholder="Ex: PETR4.SA | AAPL | BTC-USD")
        with fa2: al_tipo = st.selectbox("Disparar quando:", ["acima","abaixo"])
        with fa3: al_valor = st.number_input("Preço alvo:", min_value=0.01, value=50.00, step=0.01)
        if st.form_submit_button("➕ Adicionar Alerta", use_container_width=True):
            if al_ticker.strip():
                st.session_state.alertas_preco.append({"ticker":al_ticker.strip().upper(),"tipo":al_tipo,"valor":al_valor,"ativo":True,"criado":datetime.now().strftime("%d/%m %H:%M")})
                st.success(f"✅ Alerta adicionado para {al_ticker.upper()}")
            else:
                st.error("Informe o ticker!")

    st.markdown("---")
    ativos = [a for a in st.session_state.alertas_preco if a.get("ativo",True)]
    if ativos:
        st.markdown(f"#### 🟢 Alertas Ativos ({len(ativos)})")
        for i, alerta in enumerate(st.session_state.alertas_preco):
            if not alerta.get("ativo",True): continue
            c1,c2,c3,c4,c5 = st.columns([2,1,1,1,1])
            c1.markdown(f"<span style='font-family:Space Mono,monospace;color:#0ea5e9;'>📊 {alerta['ticker']}</span>", unsafe_allow_html=True)
            c2.markdown(f"<span style='color:#64748b;font-size:0.82rem;'>preço {alerta['tipo']}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='font-family:Space Mono,monospace;color:#f59e0b;'>{alerta['valor']:.2f}</span>", unsafe_allow_html=True)
            c4.markdown(f"<span style='color:#64748b;font-size:0.75rem;'>{alerta['criado']}</span>", unsafe_allow_html=True)
            if c5.button("🗑️", key=f"del_{i}"):
                st.session_state.alertas_preco[i]["ativo"] = False
                st.rerun()
    else:
        st.info("Nenhum alerta ativo. Crie um acima!")

    if st.session_state.alertas_disparados:
        st.markdown("---")
        st.markdown(f"#### 🔔 Disparados ({len(st.session_state.alertas_disparados)})")
        for ad in reversed(st.session_state.alertas_disparados):
            icon = "⬆️" if ad["tipo"]=="acima" else "⬇️"
            st.markdown(f"<div style='background:#f59e0b08;border:1px solid #f59e0b;border-radius:8px;padding:12px;margin:6px 0;font-family:Space Mono,monospace;font-size:0.85rem;'>{icon} <b style='color:#f59e0b;'>{ad['ticker']}</b> {ad['tipo']} {ad['valor']:.2f} → <b style='color:#00d4aa;'>{ad['preco_disparado']:.2f}</b> <span style='color:#64748b;'>[{ad['hora']}]</span></div>", unsafe_allow_html=True)
        if st.button("🧹 Limpar histórico"):
            st.session_state.alertas_disparados = []
            st.rerun()

# ═══════════════════════════════════════════════════════════════════
# ABA 3 — ÍNDICES GLOBAIS
# ═══════════════════════════════════════════════════════════════════
with abas[3]:
    st.markdown("### 📊 Índices & Mercados Globais")
    if st.button("🔄 Atualizar Índices", use_container_width=True):
        st.rerun()

    cols = st.columns(4)
    for i, (nome_idx, ticker_idx, regiao) in enumerate(INDICES):
        with cols[i%4]:
            try:
                tk = yf.Ticker(ticker_idx)
                hist = tk.history(period="2d")
                if not hist.empty and len(hist)>=2:
                    preco_at = hist["Close"].iloc[-1]
                    preco_ant = hist["Close"].iloc[-2]
                    variacao = ((preco_at - preco_ant) / preco_ant) * 100
                    cor_var = "indice-var-pos" if variacao >= 0 else "indice-var-neg"
                    sinal = "▲" if variacao >= 0 else "▼"
                    # Formatar valor
                    if preco_at > 1000:
                        val_fmt = f"{preco_at:,.0f}"
                    elif preco_at > 10:
                        val_fmt = f"{preco_at:,.2f}"
                    else:
                        val_fmt = f"{preco_at:,.4f}"
                    st.markdown(f"""<div class='indice-card' style='margin-bottom:12px;'>
<div class='indice-nome'>{regiao} · {nome_idx}</div>
<div class='indice-valor'>{val_fmt}</div>
<div class='{cor_var}'>{sinal} {abs(variacao):.2f}%</div>
</div>""", unsafe_allow_html=True)
            except:
                st.markdown(f"<div class='indice-card' style='margin-bottom:12px;'><div class='indice-nome'>{nome_idx}</div><div style='color:#64748b;font-size:0.8rem;'>Indisponível</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📈 Gráfico Comparativo")
    idx_sel = st.selectbox("Selecionar índice:", [n for n,_,_ in INDICES])
    ticker_idx_sel = next((t for n,t,_ in INDICES if n==idx_sel), "^BVSP")
    periodo_idx = st.selectbox("Período:", ["1mo","3mo","6mo","1y"], key="p_idx")
    df_idx, _ = buscar_ativo(ticker_idx_sel, periodo_idx)
    if df_idx is not None:
        st.plotly_chart(plotar_grafico(df_idx, idx_sel), use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# ABA 4 — MUNDO (PORTAL GEOPOLÍTICO)
# ═══════════════════════════════════════════════════════════════════
with abas[4]:
    st.markdown("### 🌍 Portal Mundial — Geopolítica & Economia Global")

    regioes = {
        "🇧🇷 Brasil": [("bolsa B3 Ibovespa economia Brasil mercado","pt"), ("Brazil economy finance","en")],
        "🇺🇸 EUA":    [("US economy Fed interest rates stock market","en"), ("Wall Street Nasdaq NYSE","en")],
        "🇪🇺 Europa": [("Europe economy ECB inflation eurozone","en"), ("European markets DAX FTSE","en")],
        "🇨🇳 China":  [("China economy trade yuan market","en"), ("China GDP property market","en")],
        "🌍 Geopolítica": [("geopolitics war sanctions trade conflict","en"), ("BRICS NATO G7 global economy","en")],
        "🛢️ Commodities": [("oil gold silver commodity prices","en"), ("petróleo ouro commodities mercado","pt")],
        "₿ Cripto Global": [("bitcoin ethereum crypto regulation blockchain","en"), ("cripto bitcoin ethereum mercado","pt")],
        "📰 Tudo": [("global economy finance markets","en"), ("mercado financeiro mundial economia","pt"), ("Asia Pacific markets economy","en"), ("Middle East economy oil","en")],
    }

    regiao_sel = st.radio("Região:", list(regioes.keys()), horizontal=True)

    with st.spinner("Buscando notícias do mundo..."):
        queries = regioes[regiao_sel]
        noticias_mundo = buscar_noticias_multi(queries, n_cada=8)

    if noticias_mundo:
        st.markdown(f"**{len(noticias_mundo)} notícias encontradas**")
        render_noticias(noticias_mundo, max_desc=280)
    elif not NEWS_API_KEY:
        st.info("Configure NEWS_API_KEY no .env para ver notícias.")
    else:
        st.warning("Nenhuma notícia encontrada para esta região no momento.")

# ═══════════════════════════════════════════════════════════════════
# ABA 5 — HOT NEWS
# ═══════════════════════════════════════════════════════════════════
with abas[5]:
    st.markdown("### 🔥 Hot News — Mercado em Tempo Real")
    c1,c2,c3,c4 = st.columns(4)
    q_hot = None; lang_hot = "pt"
    if c1.button("🇧🇷 Brasil",  use_container_width=True): q_hot="bolsa B3 Ibovespa economia Brasil"
    if c2.button("🌎 Global",   use_container_width=True): q_hot="stock market economy Fed interest rates"; lang_hot="en"
    if c3.button("₿ Cripto",    use_container_width=True): q_hot="bitcoin ethereum crypto blockchain"
    if c4.button("📰 Tudo",     use_container_width=True): q_hot="mercado financeiro bolsa bitcoin economia mundo"

    if q_hot:
        with st.spinner("Buscando..."):
            nots = buscar_noticias(q_hot, n=18, lang=lang_hot)
            if not nots and lang_hot=="pt": nots = buscar_noticias(q_hot, n=18, lang="en")
        if nots: render_noticias(nots, max_desc=250)
        else: st.info("Configure NEWS_API_KEY no .env.")
    else:
        st.markdown("<div style='text-align:center;padding:60px;color:#64748b;'><h2 style='font-family:Space Mono,monospace;'>→ Escolha uma categoria acima</h2></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ABAS DE CATEGORIAS (B3, EUA, Cripto, FIIs, ETFs)
# ═══════════════════════════════════════════════════════════════════
cats_map = {
    "🇧🇷 B3":  ["B3 — Bancos","B3 — Energia","B3 — Mineração","B3 — Agro","B3 — Tecnologia","B3 — Varejo","B3 — Saúde","B3 — Construção","B3 — Papel/Indústria","B3 — Transporte"],
    "🇺🇸 EUA": ["EUA — Big Tech","EUA — Mídia/Entret.","EUA — Finanças","EUA — Saúde","EUA — Energia","EUA — Consumo"],
    "₿ Cripto":["Cripto"],
    "🏢 FIIs": ["FIIs"],
    "📊 ETFs": ["ETFs BR","ETFs EUA"],
}
for aba_idx,(nome_aba,cats) in enumerate(cats_map.items()):
    with abas[6+aba_idx]:
        st.markdown(f"### {nome_aba}")
        all_tks = [t for c in cats for t in CATALOGO.get(c,[])]
        p_cat = st.selectbox("Período:",["1mo","3mo","6mo","1y"],key=f"p_{aba_idx}")
        s_cat = st.selectbox("Setor:",["Todos"]+cats,key=f"s_{aba_idx}")
        tks_cat = CATALOGO[s_cat] if s_cat!="Todos" else all_tks
        usar_ia_cat = st.checkbox("🤖 IA nas análises", value=False, key=f"ia_cat_{aba_idx}")
        if st.button(f"Carregar {nome_aba}", key=f"btn_{aba_idx}", use_container_width=True):
            res_cat = []
            bar2 = st.progress(0)
            for i,tk in enumerate(tks_cat):
                bar2.progress((i+1)/len(tks_cat))
                df,info = buscar_ativo(tk, p_cat)
                if df is not None:
                    score,pros,contras,alertas,rec,var,var1d,alvo_a,alvo_b = gerar_analise(df,tk)
                    res_cat.append((tk,df,info,score,pros,contras,alertas,rec,var,var1d,alvo_a,alvo_b))
            bar2.empty()
            res_cat.sort(key=lambda x:x[3],reverse=True)
            for tk,df,info,score,pros,contras,alertas,rec,var,var1d,alvo_a,alvo_b in res_cat:
                cor = "#00d4aa" if "COMPRA" in rec else ("#f59e0b" if "NEUTRO" in rec else "#f43f5e")
                with st.expander(f"{tk} | ${df['Close'].iloc[-1]:.2f} | {var:+.1f}% | Score {score}/100 | {rec}"):
                    for a in alertas: st.warning(a)
                    g1,g2 = st.columns([3,1])
                    with g1: st.plotly_chart(plotar_grafico(df,tk), use_container_width=True)
                    with g2:
                        st.markdown(f"<div style='background:{cor}15;border:1px solid {cor};border-radius:8px;padding:12px;'><b style='color:{cor};font-size:1.05rem;'>{rec}</b><br><span style='color:#64748b;'>Score: {score}/100</span></div>", unsafe_allow_html=True)
                        st.markdown(f"**RSI:** {df['RSI'].iloc[-1]:.1f}")
                        if alvo_a: st.markdown(f"🎯 **Alvo:** ${alvo_a}")
                        if alvo_b: st.markdown(f"🛡️ **Stop:** ${alvo_b}")
                        with st.form(key=f"form_{tk}_{aba_idx}"):
                            val_f = st.number_input("Alerta acima de:", value=round(df['Close'].iloc[-1]*1.05,2), step=0.01)
                            if st.form_submit_button("🔔 Criar Alerta"):
                                st.session_state.alertas_preco.append({"ticker":tk,"tipo":"acima","valor":val_f,"ativo":True,"criado":datetime.now().strftime("%d/%m %H:%M")})
                                st.success("✅")
                        tp,tc = st.tabs(["✅","❌"])
                        with tp:
                            for p in pros: st.write(p)
                        with tc:
                            for c_ in contras: st.write(c_)
                    if usar_ia_cat and ANTHROPIC_KEY:
                        st.markdown("---")
                        with st.spinner("Claude analisando..."):
                            ai_txt, ai_err = analisar_com_claude(tk, df, info, score, pros, contras, rec, var, var1d, alvo_a, alvo_b)
                        if not ai_err:
                            st.markdown(f"<div class='ai-card'><div class='ai-label'>⚡ Claude AI</div><div class='ai-text'>{ai_txt.replace(chr(10),'<br>')}</div></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ABA 11 — FUNDOS DE INVESTIMENTO
# ═══════════════════════════════════════════════════════════════════
with abas[11]:
    st.markdown("### 💼 Fundos de Investimento — Radar")
    st.markdown("<p style='color:#64748b;font-family:Space Mono,monospace;font-size:0.82rem;'>Referência de retornos estimados. Consulte seu assessor para valores atualizados.</p>", unsafe_allow_html=True)

    df_fundos = pd.DataFrame(FUNDOS, columns=["Fundo","Tipo","Rentab. Est.","Risco","Rating"])
    st.dataframe(df_fundos, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### 📊 Comparativo por Tipo")
    tipo_sel = st.multiselect("Filtrar por tipo:", ["Renda Fixa","Multimercado","Renda Variável","Previdência"], default=["Renda Fixa","Multimercado"])
    fundos_filtrados = [f for f in FUNDOS if f[1] in tipo_sel]
    if fundos_filtrados:
        for f in fundos_filtrados:
            cor_risco = {"Baixo":"#00d4aa","Médio":"#f59e0b","Médio-Alto":"#f59e0b","Alto":"#f43f5e"}.get(f[3],"#64748b")
            st.markdown(f"""<div style='background:var(--surface,#0e1318);border:1px solid #1a2332;border-left:4px solid {cor_risco};border-radius:10px;padding:14px;margin:6px 0;'>
<b style='color:#e2e8f0;font-size:1rem;'>{f[0]}</b>
<span style='background:{cor_risco}22;color:{cor_risco};border:1px solid {cor_risco};padding:2px 10px;border-radius:20px;margin-left:8px;font-size:0.78rem;font-weight:700;'>{f[1]}</span>
<br><span style='color:#64748b;font-size:0.85rem;'>Rentabilidade: <b style='color:#e2e8f0;'>{f[2]}</b> &nbsp;|&nbsp; Risco: <b style='color:{cor_risco};'>{f[3]}</b> &nbsp;|&nbsp; Rating: <b style='color:#0ea5e9;'>{f[4]}</b></span>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 💡 Buscar Notícias de Fundos")
    if st.button("🔍 Notícias sobre fundos de investimento"):
        with st.spinner("Buscando..."):
            nots_f = buscar_noticias("fundos investimento BTG XP Itaú gestora retorno", n=8)
        if nots_f: render_noticias(nots_f)

# ═══════════════════════════════════════════════════════════════════
# ABA 12 — RENDA FIXA
# ═══════════════════════════════════════════════════════════════════
with abas[12]:
    st.markdown("### 💰 Renda Fixa — Radar e Simulador")
    df_rf = pd.DataFrame({
        "Produto":  ["Tesouro Selic 2029","Tesouro IPCA+2035","CDB 100% CDI","CDB 120% CDI","LCI 90% CDI","LCA 92% CDI","Debênture IPCA+7%","CRI IPCA+8%"],
        "Rentab.":  ["~14.75%","IPCA+7.5%","~14.75%","~17.7%","~13.3%","~13.6%","IPCA+7%","IPCA+8%"],
        "IR":       ["Sim","Sim","Sim","Sim","Isento","Isento","Sim/Isento","Isento"],
        "Liquidez": ["Diária","Vencto","Vencto","Vencto","Vencto","Vencto","Vencto","Vencto"],
        "FGC":      ["Não","Não","Sim","Sim","Sim","Sim","Não","Não"],
        "Score":    [90,87,78,88,76,77,85,88]
    }).sort_values("Score",ascending=False)
    st.dataframe(df_rf, use_container_width=True, hide_index=True)

    r1,r2,r3,r4 = st.columns(4)
    with r1: valor=st.number_input("Capital (R$):",value=10000,step=1000)
    with r2: taxa=st.number_input("Taxa anual (%):",value=14.75,step=0.25)
    with r3: meses=st.slider("Prazo (meses):",1,120,12)
    with r4: ir_op=st.selectbox("IR:",["Sim","Isento"])
    taxa_m=(1+taxa/100)**(1/12)-1
    meses_r=list(range(1,meses+1)); valores=[valor*(1+taxa_m)**m for m in meses_r]
    rend=valores[-1]-valor
    aliq=0.225 if meses<=6 else (0.20 if meses<=12 else (0.175 if meses<=24 else 0.15)) if ir_op=="Sim" else 0
    fig_rf=go.Figure()
    fig_rf.add_trace(go.Scatter(x=meses_r,y=valores,fill="tozeroy",line=dict(color="#00d4aa",width=2),name="Patrimônio"))
    fig_rf.update_layout(template="plotly_dark",height=280,paper_bgcolor="#080c10",plot_bgcolor="#080c10",margin=dict(l=40,r=20,t=20,b=40))
    st.plotly_chart(fig_rf,use_container_width=True)
    s1,s2,s3=st.columns(3)
    s1.metric("Patrimônio Bruto",f"R$ {valores[-1]:,.2f}")
    s2.metric("Rendimento Líquido",f"R$ {rend*(1-aliq):,.2f}")
    s3.metric("IR Pago",f"R$ {rend*aliq:,.2f}" if aliq>0 else "Isento")

# ═══════════════════════════════════════════════════════════════════
# ABA 13 — NEWSLETTER
# ═══════════════════════════════════════════════════════════════════
with abas[13]:
    st.markdown("### 📧 Newsletter & Alertas Automáticos")
    st.info(f"📬 Configurado para: **{GMAIL_USER or 'Configure GMAIL_USER no .env'}**")
    st.markdown("""
A newsletter inclui:
- 🟢 **Oportunidades de Compra** identificadas pela IA
- 🔴 **Sinais de Venda / Cautela**
- 💡 **Mensagem do Dia** gerada pelo Claude
- 🇧🇷 **Notícias do Mercado Brasileiro**
- 🇺🇸 **Notícias do Mercado Americano**
- 🌍 **Geopolítica & Mundo**
- 🔗 Links clicáveis para todas as notícias

Envio automático: **07:00 · 13:00 · 18:00**
""")
    n1,n2=st.columns(2)
    with n1:
        if st.button("📤 Enviar Newsletter Agora", use_container_width=True):
            with st.spinner("Analisando mercado e montando newsletter..."):
                ok=gerar_newsletter()
            if ok: st.success(f"✅ Enviado para {GMAIL_USER}!")
            else:  st.error("❌ Erro. Verifique GMAIL_USER e GMAIL_PASS no .env")
    with n2:
        if st.button("🧪 Testar Gmail", use_container_width=True):
            ok=enviar_email("✅ Teste TradeBot","<h2 style='color:#00d4aa;'>Funcionando! 🚀</h2>")
            if ok: st.success("✅ Gmail conectado!")
            else:  st.error("❌ Falha — verifique as credenciais")
    st.markdown("---")
    st.markdown("#### ⏰ Próximos Envios")
    agora=datetime.now()
    for hora in ["07:00","13:00","18:00"]:
        h,m_=map(int,hora.split(":"))
        prox=agora.replace(hour=h,minute=m_,second=0)
        if prox<agora: prox+=timedelta(days=1)
        diff=prox-agora; hr=int(diff.seconds//3600); mn=int((diff.seconds%3600)//60)
        st.markdown(f"<span style='font-family:Space Mono,monospace;color:#64748b;'>🕐 **{hora}** — em {hr}h {mn}min</span>", unsafe_allow_html=True)
