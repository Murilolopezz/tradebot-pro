"""
config.py — Configurações, segredos e catálogos estáticos.
Altere aqui: credenciais, listas de ativos, índices, fundos.
"""
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _secret(key, default=""):
    val = os.getenv(key, "")
    if not val:
        try:
            val = st.secrets.get(key, default)
        except Exception:
            pass
    return str(val) if val else default


# ── Credenciais / flags ───────────────────────────────────────────────────────
GMAIL_USER    = _secret("GMAIL_USER")
GMAIL_PASS    = _secret("GMAIL_PASS")
NEWS_API_KEY  = _secret("NEWS_API_KEY")
ANTHROPIC_KEY = _secret("ANTHROPIC_API_KEY")
APP_PASSWORD  = _secret("APP_PASSWORD", "tradebot2024")
MANUTENCAO    = _secret("MANUTENCAO", "false").lower() == "true"
ADMIN_PASS    = _secret("ADMIN_PASS", "admin2024")

SUBSCRIBERS_FILE = "subscribers.json"

# ── Catálogo de ativos ────────────────────────────────────────────────────────
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

# ── Índices globais ───────────────────────────────────────────────────────────
INDICES = [
    ("Ibovespa",  "^BVSP",   "BR"),
    ("S&P 500",   "^GSPC",   "EUA"),
    ("Nasdaq",    "^IXIC",   "EUA"),
    ("Dow Jones", "^DJI",    "EUA"),
    ("DAX",       "^GDAXI",  "EU"),
    ("FTSE 100",  "^FTSE",   "EU"),
    ("Nikkei",    "^N225",   "ASIA"),
    ("Hang Seng", "^HSI",    "ASIA"),
    ("Ouro",      "GC=F",    "Comod."),
    ("Petróleo",  "CL=F",    "Comod."),
    ("Dólar/BRL", "USDBRL=X","FX"),
    ("Bitcoin",   "BTC-USD", "Cripto"),
]

# ── Fundos de investimento ────────────────────────────────────────────────────
FUNDOS = [
    ("Butiá Excellence FIC",    "Renda Fixa",     "~13.5% a.a.", "Baixo",     "AAA"),
    ("BTG Pactual Tesouro Selic","Renda Fixa",    "~15.0% a.a.", "Baixo",     "AAA"),
    ("Verde AM",                 "Multimercado",   "CDI+5%~8%",   "Médio",     "A+"),
    ("SPX Nimitz",               "Multimercado",   "CDI+6%~10%",  "Médio-Alto","A+"),
    ("Kinea Prev XP",            "Previdência",    "CDI+4%",      "Médio",     "AA"),
    ("ARX Income",               "Renda Fixa",     "CDI+1.5%",    "Baixo",     "AA"),
    ("Kapitalo Kappa",           "Multimercado",   "CDI+7%",      "Alto",      "A"),
    ("Ibiuna Hedge",             "Multimercado",   "CDI+5%",      "Médio",     "A+"),
    ("XP Long Biased",           "Renda Variável", "IBOV+5%",     "Alto",      "A"),
    ("BTG Absoluto",             "Multimercado",   "CDI+8%",      "Alto",      "A"),
]
