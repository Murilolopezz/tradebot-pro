"""
send_newsletter.py — Script autônomo para envio da newsletter.
Roda via GitHub Actions (cron) sem depender do Streamlit.
"""

import os
import smtplib
import requests
import pandas as pd
import numpy as np
import yfinance as yf
import anthropic
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ─── Configurações ────────────────────────────────────────────────────────────
GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_PASS     = os.getenv("GMAIL_PASS", "")
NEWS_API_KEY   = os.getenv("NEWS_API_KEY", "")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
# Lista de inscritos separada por vírgula no GitHub Secret:
# Ex: "fulano@gmail.com,ciclano@hotmail.com"
SUBSCRIBERS_LIST = os.getenv("SUBSCRIBERS_LIST", "")

# ─── Ativos analisados na newsletter ─────────────────────────────────────────
AMOSTRA = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "WEGE3.SA",
    "PRIO3.SA", "KLBN11.SA", "AAPL", "NVDA", "MSFT",
    "BTC-USD", "ETH-USD", "BBAS3.SA"
]

# ─── Funções auxiliares ───────────────────────────────────────────────────────
def calcular_indicadores(df):
    df = df.copy()
    df["SMA20"]  = df["Close"].rolling(20).mean()
    df["SMA50"]  = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["RSI"]    = 100 - (100 / (1 + gain / loss))
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]   = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"]  - df["Close"].shift()).abs()
    ], axis=1).max(axis=1)
    df["ATR"]      = tr.rolling(14).mean()
    df["Vol_media"]= df["Volume"].rolling(20).mean()
    df["BB_mid"]   = df["Close"].rolling(20).mean()
    std            = df["Close"].rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2 * std
    df["BB_lower"] = df["BB_mid"] - 2 * std
    return df

def gerar_analise(df, ticker):
    ultimo = df["Close"].iloc[-1]
    sma20  = df["SMA20"].iloc[-1]
    sma50  = df["SMA50"].iloc[-1]
    sma200 = df["SMA200"].iloc[-1]
    rsi    = df["RSI"].iloc[-1]
    macd   = df["MACD"].iloc[-1]
    signal = df["Signal"].iloc[-1]
    atr    = df["ATR"].iloc[-1]
    bb_up  = df["BB_upper"].iloc[-1]
    bb_low = df["BB_lower"].iloc[-1]
    vol_at = df["Volume"].iloc[-1]
    vol_md = df["Vol_media"].iloc[-1]
    var    = ((ultimo - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100
    macd_prev = df["MACD"].iloc[-2]
    sig_prev  = df["Signal"].iloc[-2]
    score = 50; alertas = []
    if ultimo > sma20:  score += 8
    else:               score -= 8
    if ultimo > sma50:  score += 10
    else:               score -= 10
    if not pd.isna(sma200):
        if ultimo > sma200: score += 12
        else:               score -= 12
    if rsi < 30:    score += 18; alertas.append(f"🟢 RSI {rsi:.1f} — SOBREVENDA")
    elif rsi < 45:  score += 8
    elif rsi > 70:  score -= 15; alertas.append(f"🔴 RSI {rsi:.1f} — SOBRECOMPRA")
    elif rsi > 60:  score += 5
    else:           score += 3
    if macd > signal and macd_prev <= sig_prev:
        score += 15; alertas.append("🔔 Cruzamento MACD alta")
    elif macd > signal: score += 8
    elif macd < signal and macd_prev >= sig_prev:
        score -= 15; alertas.append("⚠️ Cruzamento MACD baixa")
    else:           score -= 8
    if ultimo <= bb_low: score += 10
    elif ultimo >= bb_up: score -= 10
    if not pd.isna(vol_md) and vol_md > 0:
        vr = vol_at / vol_md
        if vr > 2:    score += 8
        elif vr < 0.5: score -= 5
    if var > 0: score += 5
    else:       score -= 5
    score = max(0, min(100, score))
    if score >= 75:   rec = "🟢 FORTE COMPRA"
    elif score >= 60: rec = "🟩 COMPRA"
    elif score >= 45: rec = "🟡 NEUTRO"
    elif score >= 30: rec = "🟠 VENDA PARCIAL"
    else:             rec = "🔴 VENDA / EVITAR"
    alvo_a = round(ultimo * (1 + (atr / ultimo) * 3), 2) if not pd.isna(atr) else None
    alvo_b = round(ultimo * (1 - (atr / ultimo) * 2), 2) if not pd.isna(atr) else None
    return score, rec, var, alertas, alvo_a, alvo_b

def buscar_ativo(ticker):
    try:
        d = yf.Ticker(ticker)
        h = d.history(period="1mo")
        if h.empty or len(h) < 20: return None
        h.index = h.index.tz_localize(None) if h.index.tz else h.index
        return calcular_indicadores(h)
    except:
        return None

def buscar_noticias(query, n=4, lang="pt"):
    if not NEWS_API_KEY: return []
    try:
        r = requests.get(
            f"https://newsapi.org/v2/everything?q={query}"
            f"&language={lang}&sortBy=publishedAt&pageSize={n}"
            f"&apiKey={NEWS_API_KEY}",
            timeout=10
        )
        arts = r.json().get("articles", [])
        if not arts and lang == "pt":
            r2 = requests.get(
                f"https://newsapi.org/v2/everything?q={query}"
                f"&language=en&sortBy=publishedAt&pageSize={n}"
                f"&apiKey={NEWS_API_KEY}",
                timeout=10
            )
            arts = r2.json().get("articles", [])
        return [a for a in arts if a.get("title") and a.get("title") != "[Removed]"]
    except:
        return []

def enviar_email(assunto, corpo, destinatario):
    if not GMAIL_USER or not GMAIL_PASS: return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"]    = GMAIL_USER
        msg["To"]      = destinatario
        msg.attach(MIMEText(corpo, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.sendmail(GMAIL_USER, destinatario, msg.as_string())
        return True
    except Exception as e:
        print(f"  ✗ Erro ao enviar para {destinatario}: {e}")
        return False

# ─── Geração do conteúdo ──────────────────────────────────────────────────────
def gerar_corpo_newsletter():
    print("📊 Analisando ativos...")
    compras, vendas = [], []
    for tk in AMOSTRA:
        df = buscar_ativo(tk)
        if df is not None:
            score, rec, var, alertas, alvo_a, alvo_b = gerar_analise(df, tk)
            entry = (tk, score, rec, var, alertas)
            if "COMPRA" in rec:                compras.append(entry)
            elif "VENDA" in rec or score < 40: vendas.append(entry)
    compras.sort(key=lambda x: x[1], reverse=True)
    vendas.sort(key=lambda x: x[1])
    print(f"  → {len(compras)} oportunidades de compra | {len(vendas)} sinais de venda")

    def bloco_ativo(tk, score, rec, var, alertas):
        cor = "#00d4aa" if "COMPRA" in rec else "#f43f5e"
        return (
            f'<div style="background:#0e1318;border:1px solid #1a2332;'
            f'border-left:4px solid {cor};border-radius:10px;padding:14px;margin:8px 0;">'
            f'<b style="color:#0ea5e9;font-size:1.05rem;">{tk}</b>'
            f'<span style="background:{cor};color:#000;padding:2px 10px;border-radius:20px;'
            f'margin-left:8px;font-weight:700;font-size:0.82rem;">{rec}</span>'
            f'<br><span style="color:#64748b;font-size:0.85rem;">Score: {score}/100 &nbsp;|&nbsp; '
            f'Var: {var:+.1f}%</span>'
            + "".join(f'<br><span style="color:#f59e0b;font-size:0.82rem;">⚡ {a}</span>' for a in alertas)
            + "</div>"
        )

    # Mensagem do dia via Claude
    print("🤖 Gerando mensagem do dia com Claude...")
    msg_dia = "O mercado recompensa quem estuda, planeja e mantém a disciplina. Bons trades hoje!"
    if ANTHROPIC_KEY:
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            r = client.messages.create(
                model="claude-opus-4-6", max_tokens=200,
                messages=[{"role": "user", "content":
                    f"Escreva uma mensagem motivacional e inteligente de 2-3 frases para "
                    f"investidores para o dia {datetime.now().strftime('%d/%m/%Y')}. "
                    f"Mencione algo relevante sobre o mercado financeiro atual. Seja inspirador mas realista."
                }]
            )
            msg_dia = r.content[0].text
            print("  → Mensagem gerada com sucesso")
        except Exception as e:
            print(f"  ✗ Claude indisponível: {e}")

    # Notícias
    print("📰 Buscando notícias...")
    nots_br     = buscar_noticias("bolsa B3 Ibovespa Brasil mercado", n=4)
    nots_us     = buscar_noticias("stock market NYSE Nasdaq Fed", n=4, lang="en")
    nots_global = buscar_noticias("global economy geopolitics trade war", n=3, lang="en")

    def bloco_noticias(noticias, titulo, cor):
        html = f"<h3 style='color:{cor};margin-top:20px;'>{titulo}</h3>"
        for n in noticias:
            url   = n.get("url", "#")
            t     = n.get("title", "")
            fonte = n.get("source", {}).get("name", "")
            data  = n.get("publishedAt", "")[:10]
            html += (
                f'<div style="background:#0e1318;border-left:3px solid {cor};'
                f'padding:10px 14px;margin:6px 0;border-radius:6px;">'
                f'<a href="{url}" style="color:#e2e8f0;text-decoration:none;'
                f'font-weight:600;font-size:0.92rem;">{t}</a>'
                f'<br><span style="color:#64748b;font-size:0.78rem;">{fonte} — {data}</span></div>'
            )
        return html

    corpo = f"""<html><body style="background:#080c10;color:#e2e8f0;font-family:Arial,sans-serif;padding:24px;max-width:700px;margin:auto;">
<h1 style="color:#00d4aa;border-bottom:2px solid #1a2332;padding-bottom:12px;">📈 MbInvest Bot Pro — Newsletter</h1>
<p style="color:#64748b;font-family:monospace;">{datetime.now().strftime("%d/%m/%Y %H:%M")} — Análise automatizada via GitHub Actions</p>

<div style="background:linear-gradient(135deg,#0a1628,#0d1f3c);border:1px solid #1a3a5c;border-radius:12px;padding:18px;margin:16px 0;">
<div style="color:#00d4aa;font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">💡 Mensagem do Dia</div>
<p style="color:#e2e8f0;line-height:1.7;margin:0;">{msg_dia}</p>
</div>

<h2 style="color:#00d4aa;">🟢 Oportunidades de Compra</h2>
{"".join(bloco_ativo(*c) for c in compras[:5]) if compras else "<p style='color:#64748b;'>Nenhuma oportunidade de compra identificada hoje.</p>"}

<h2 style="color:#f43f5e;">🔴 Sinais de Venda / Cautela</h2>
{"".join(bloco_ativo(*v) for v in vendas[:4]) if vendas else "<p style='color:#64748b;'>Nenhum sinal de venda identificado hoje.</p>"}

<hr style="border-color:#1a2332;margin:24px 0;">
{bloco_noticias(nots_br, "🇧🇷 Mercado Brasileiro", "#00d4aa")}
{bloco_noticias(nots_us, "🇺🇸 Mercado Americano", "#0ea5e9")}
{bloco_noticias(nots_global, "🌍 Geopolítica & Mundo", "#f59e0b")}

<p style="color:#64748b;font-size:0.75rem;margin-top:24px;text-align:center;">
MbInvest Bot Pro · Este email é informativo e não constitui recomendação de investimento.<br>
Para cancelar sua inscrição, entre em contato com o administrador.
</p>
</body></html>"""
    return corpo

# ─── Execução principal ───────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"📧 MbInvest Bot Pro — Newsletter  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*60}")

    if not GMAIL_USER or not GMAIL_PASS:
        print("❌ GMAIL_USER e GMAIL_PASS não configurados. Abortando.")
        return

    # Montar lista de destinatários
    destinatarios = []
    if GMAIL_USER:
        destinatarios.append(GMAIL_USER)
    if SUBSCRIBERS_LIST:
        extras = [e.strip().lower() for e in SUBSCRIBERS_LIST.split(",") if e.strip()]
        destinatarios.extend(e for e in extras if e not in destinatarios)
    destinatarios = list(dict.fromkeys(destinatarios))  # deduplica
    print(f"👥 Destinatários: {len(destinatarios)}")

    corpo = gerar_corpo_newsletter()
    assunto = f"📈 MbInvest Bot Pro — {datetime.now().strftime('%d/%m')} · Oportunidades do Dia"

    print(f"\n📤 Enviando newsletter...")
    ok = erros = 0
    for dest in destinatarios:
        if enviar_email(assunto, corpo, dest):
            print(f"  ✓ Enviado → {dest}")
            ok += 1
        else:
            erros += 1

    print(f"\n{'='*60}")
    print(f"✅ {ok} enviado(s) | ❌ {erros} erro(s)")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
