"""
data.py — Busca e processamento de dados de ativos (Yahoo Finance).
Altere aqui: indicadores técnicos, período de dados, fonte de preços.
"""
import yfinance as yf
import pandas as pd


def calcular_indicadores(df):
    df = df.copy()
    df["SMA20"]    = df["Close"].rolling(20).mean()
    df["SMA50"]    = df["Close"].rolling(50).mean()
    df["SMA200"]   = df["Close"].rolling(200).mean()
    df["EMA9"]     = df["Close"].ewm(span=9,  adjust=False).mean()
    df["EMA21"]    = df["Close"].ewm(span=21, adjust=False).mean()
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["RSI"]    = 100 - (100 / (1 + gain / loss))
    ema12        = df["Close"].ewm(span=12, adjust=False).mean()
    ema26        = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]   = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["Hist"]   = df["MACD"] - df["Signal"]
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"]  - df["Close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["ATR"]      = tr.rolling(14).mean()
    df["BB_mid"]   = df["Close"].rolling(20).mean()
    std            = df["Close"].rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2 * std
    df["BB_lower"] = df["BB_mid"] - 2 * std
    df["Vol_media"]= df["Volume"].rolling(20).mean()
    return df


def buscar_ativo(ticker, periodo):
    try:
        d = yf.Ticker(ticker)
        h = d.history(period=periodo)
        if h.empty or len(h) < 30:
            return None, None
        h.index = h.index.tz_localize(None) if h.index.tz is not None else h.index
        return calcular_indicadores(h), d.info
    except:
        return None, None
