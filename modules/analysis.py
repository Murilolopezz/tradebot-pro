"""
analysis.py — Score técnico e análise por IA (Claude).
Altere aqui: lógica de pontuação, pesos dos indicadores, prompt da IA.
"""
import pandas as pd
import anthropic
from modules.config import ANTHROPIC_KEY


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
    var1d  = ((ultimo - df["Close"].iloc[-2]) / df["Close"].iloc[-2]) * 100 if len(df) > 1 else 0

    score = 50
    pros, contras, alertas = [], [], []

    if ultimo > sma20: score += 8;  pros.append("📈 Preço acima da SMA20 — momentum positivo")
    else:              score -= 8;  contras.append("📉 Preço abaixo da SMA20 — pressão vendedora")

    if ultimo > sma50: score += 10; pros.append("✅ Acima da SMA50 — tendência intermediária de alta")
    else:              score -= 10; contras.append("⚠️ Abaixo da SMA50 — tendência intermediária de baixa")

    sma200 = df["SMA200"].iloc[-1]
    if not pd.isna(sma200):
        if ultimo > sma200: score += 12; pros.append("🏆 Acima da SMA200 — bull market de longo prazo")
        else:               score -= 12; contras.append("🐻 Abaixo da SMA200 — bear market de longo prazo")

    if rsi < 30:   score += 18; pros.append(f"🟢 RSI {rsi:.1f} — SOBREVENDA! Possível reversão");    alertas.append("🔔 RSI em sobrevenda — oportunidade!")
    elif rsi < 45: score += 8;  pros.append(f"📊 RSI {rsi:.1f} — fraqueza, possível recuperação")
    elif rsi > 70: score -= 15; contras.append(f"🔴 RSI {rsi:.1f} — SOBRECOMPRA! Risco de correção"); alertas.append("⚠️ RSI em sobrecompra — cuidado!")
    elif rsi > 60: score += 5;  pros.append(f"📊 RSI {rsi:.1f} — força moderada")
    else:          score += 3;  pros.append(f"📊 RSI {rsi:.1f} — zona neutra")

    macd_prev = df["MACD"].iloc[-2]; sig_prev = df["Signal"].iloc[-2]
    if macd > signal and macd_prev <= sig_prev:
        score += 15; pros.append("🚀 Cruzamento MACD para cima — sinal de COMPRA!"); alertas.append("🔔 Cruzamento de alta no MACD!")
    elif macd > signal:
        score += 8;  pros.append("✅ MACD positivo — momentum favorável")
    elif macd < signal and macd_prev >= sig_prev:
        score -= 15; contras.append("💀 Cruzamento MACD para baixo — sinal de VENDA!"); alertas.append("⚠️ Cruzamento de baixa no MACD!")
    else:
        score -= 8;  contras.append("❌ MACD negativo — momentum desfavorável")

    if ultimo <= bb_low:  score += 10; pros.append("🎯 Na banda inferior de Bollinger — suporte/reversão")
    elif ultimo >= bb_up: score -= 10; contras.append("⚡ Na banda superior de Bollinger — sobreextensão")

    if not pd.isna(vol_md) and vol_md > 0:
        vr = vol_at / vol_md
        if vr > 2:    score += 8; pros.append(f"📊 Volume {vr:.1f}x acima da média — forte interesse")
        elif vr < 0.5: score -= 5; contras.append("😴 Volume abaixo da média")

    if var > 0: score += 5; pros.append(f"📈 +{var:.1f}% no período")
    else:       score -= 5; contras.append(f"📉 {var:.1f}% no período")

    score = max(0, min(100, score))
    if score >= 75:   rec = "🟢 FORTE COMPRA"
    elif score >= 60: rec = "🟩 COMPRA"
    elif score >= 45: rec = "🟡 NEUTRO"
    elif score >= 30: rec = "🟠 VENDA PARCIAL"
    else:             rec = "🔴 VENDA / EVITAR"

    alvo_a = round(ultimo * (1 + (atr / ultimo) * 3), 2) if not pd.isna(atr) else None
    alvo_b = round(ultimo * (1 - (atr / ultimo) * 2), 2) if not pd.isna(atr) else None
    return score, pros, contras, alertas, rec, var, var1d, alvo_a, alvo_b


def analisar_com_claude(ticker, df, info, score, pros, contras, rec, var, var1d, alvo_a, alvo_b):
    if not ANTHROPIC_KEY:
        return None, "Configure ANTHROPIC_API_KEY no .env."
    try:
        from datetime import datetime
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        preco  = df["Close"].iloc[-1]
        rsi    = df["RSI"].iloc[-1]
        macd   = df["MACD"].iloc[-1]
        signal = df["Signal"].iloc[-1]
        atr    = df["ATR"].iloc[-1]
        nome   = info.get("longName", ticker) if info else ticker
        setor  = info.get("sector", "N/A")    if info else "N/A"
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
        msg = client.messages.create(
            model="claude-opus-4-6", max_tokens=700,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text, None
    except Exception as e:
        return None, f"Erro IA: {str(e)}"
