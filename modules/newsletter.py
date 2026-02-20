"""
newsletter.py — Geração e envio da newsletter + verificação de alertas.
Altere aqui: citações, ativos analisados, horários de envio, layout do email.
"""
import random
import schedule
import time
import threading
import yfinance as yf
from datetime import datetime

import streamlit as st

from modules.config   import GMAIL_USER, ANTHROPIC_KEY, ADMIN_PASS
from modules.data     import buscar_ativo
from modules.analysis import gerar_analise
from modules.news     import _fetch_noticias_raw
from modules.email_utils import enviar_email, carregar_subscribers


# ── Citações de grandes investidores e pensadores econômicos ──────────────────
# Altere ou adicione citações aqui sem afetar nenhuma outra função do app.
QUOTES_INVESTIDORES = [
    ("O preço é o que você paga. O valor é o que você recebe.",
     "Warren Buffett"),
    ("Seja temeroso quando os outros são gananciosos, e ganancioso quando os outros são temerosos.",
     "Warren Buffett"),
    ("Nunca invista num negócio que você não consiga entender.",
     "Warren Buffett"),
    ("A bolsa é um dispositivo para transferir dinheiro do impaciente para o paciente.",
     "Warren Buffett"),
    ("Regra nº 1: nunca perca dinheiro. Regra nº 2: nunca esqueça a regra nº 1.",
     "Warren Buffett"),
    ("Nosso período favorito de retenção é para sempre.",
     "Warren Buffett"),
    ("O risco vem de não saber o que você está fazendo.",
     "Warren Buffett"),
    ("Diversificação é proteção contra a ignorância. Faz pouco sentido para quem sabe o que está fazendo.",
     "Warren Buffett"),
    ("No curto prazo, o mercado é uma máquina de votos. No longo prazo, é uma balança.",
     "Benjamin Graham"),
    ("O investidor individual deve agir consistentemente como investidor, não como especulador.",
     "Benjamin Graham"),
    ("Margem de segurança é o conceito central do investimento em valor.",
     "Benjamin Graham"),
    ("O mercado não é um mecanismo de pagamento automático; ele recompensa quem pensa claramente.",
     "Benjamin Graham"),
    ("Operações de investimento são aquelas que, após análise profunda, prometem segurança do principal e retorno adequado.",
     "Benjamin Graham"),
    ("Invista no que você conhece.",
     "Peter Lynch"),
    ("Por trás de cada ação há uma empresa. Descubra o que ela está fazendo.",
     "Peter Lynch"),
    ("Muito mais dinheiro foi perdido por investidores se preparando para correções do que nas próprias correções.",
     "Peter Lynch"),
    ("A chave do investimento não é avaliar quanto uma indústria vai afetar a sociedade, mas a vantagem competitiva de cada empresa.",
     "Peter Lynch"),
    ("Os mercados nunca estão errados — as opiniões frequentemente estão.",
     "Jesse Livermore"),
    ("Nunca argumente com a fita do mercado.",
     "Jesse Livermore"),
    ("A paciência é uma virtude rara em Wall Street.",
     "Jesse Livermore"),
    ("Inverta, sempre inverta.",
     "Charlie Munger"),
    ("Mostre-me o incentivo e eu te mostrarei o resultado.",
     "Charlie Munger"),
    ("Não basta ter boas ações; é preciso ter paciência para segurá-las.",
     "Charlie Munger"),
    ("Toda grande empresa foi pequena um dia.",
     "Philip Fisher"),
    ("Concentre-se no que a empresa irá lucrar daqui a dez anos.",
     "Philip Fisher"),
    ("Não tente prever o mercado. Posicione-se bem e deixe o tempo trabalhar a seu favor.",
     "Howard Marks"),
    ("Os maiores erros de investimento vêm de erros psicológicos, não analíticos.",
     "Howard Marks"),
    ("O sucesso no investimento não é acertar sempre — é ter razão mais vezes do que errar, e ganhar mais quando acerta.",
     "Howard Marks"),
    ("Os princípios corretos aplicados consistentemente ao longo do tempo criam resultados extraordinários.",
     "Ray Dalio"),
    ("Entenda sua máquina econômica e ajuste quando necessário.",
     "Ray Dalio"),
    ("Dor + Reflexão = Progresso.",
     "Ray Dalio"),
    ("O conhecimento local é o conhecimento mais útil de todos.",
     "Friedrich Hayek"),
    ("Os preços são instrumentos de comunicação que coordenam o conhecimento disperso na sociedade.",
     "Friedrich Hayek"),
    ("A liberdade econômica é condição necessária para a liberdade política.",
     "Friedrich Hayek"),
    ("O poder tende a corromper, e o poder absoluto corrompe absolutamente.",
     "Lord Acton"),
    ("A dificuldade não está nas novas ideias, mas em escapar das antigas.",
     "John Maynard Keynes"),
    ("Os mercados podem permanecer irracionais por mais tempo do que você pode permanecer solvente.",
     "John Maynard Keynes"),
    ("Quando os fatos mudam, eu mudo minha opinião. E você?",
     "John Maynard Keynes"),
    ("O tempo no mercado bate o timing do mercado.",
     "Ken Fisher"),
    ("Compre quando há sangue nas ruas, mesmo que o sangue seja seu.",
     "Baron Rothschild"),
    ("Uma empresa que não corre riscos dificilmente prosperará.",
     "John D. Rockefeller"),
    ("A paciência é a maior virtude do investidor de longo prazo.",
     "John C. Bogle"),
    ("Mantenha os custos baixos, diversifique e seja paciente.",
     "John C. Bogle"),
]


def sortear_citacao():
    """Retorna uma citação aleatória no formato HTML para a newsletter."""
    frase, autor = random.choice(QUOTES_INVESTIDORES)
    return frase, autor


# ── Newsletter ────────────────────────────────────────────────────────────────

def gerar_newsletter():
    amostra = [
        "PETR4.SA","VALE3.SA","ITUB4.SA","WEGE3.SA","PRIO3.SA",
        "KLBN11.SA","AAPL","NVDA","MSFT","BTC-USD","ETH-USD","BBAS3.SA",
    ]
    compras, vendas = [], []
    for tk in amostra:
        df, _ = buscar_ativo(tk, "1mo")
        if df is not None:
            score, _, _, alertas, rec, var, _, _, _ = gerar_analise(df, tk)
            entry = (tk, score, rec, var, alertas)
            if "COMPRA" in rec:
                compras.append(entry)
            elif "VENDA" in rec or score < 40:
                vendas.append(entry)
    compras.sort(key=lambda x: x[1], reverse=True)
    vendas.sort(key=lambda x: x[1])

    def bloco_ativo(tk, score, rec, var, alertas):
        cor = "#00d4aa" if "COMPRA" in rec else "#f43f5e"
        return f"""<div style="background:#0e1318;border:1px solid #1a2332;border-left:4px solid {cor};border-radius:10px;padding:14px;margin:8px 0;">
<b style="color:#0ea5e9;font-size:1.05rem;">{tk}</b>
<span style="background:{cor};color:#000;padding:2px 10px;border-radius:20px;margin-left:8px;font-weight:700;font-size:0.82rem;">{rec}</span>
<br><span style="color:#64748b;font-size:0.85rem;">Score: {score}/100 &nbsp;|&nbsp; Var: {var:+.1f}%</span>
{"".join(f"<br><span style='color:#f59e0b;font-size:0.82rem;'>⚡ {a}</span>" for a in alertas)}
</div>"""

    # ── Citação do dia ────────────────────────────────────────────────────────
    frase, autor = sortear_citacao()

    # ── Notícias recentes ─────────────────────────────────────────────────────
    nots_br     = _fetch_noticias_raw("bolsa B3 Ibovespa Brasil mercado financeiro", n=5, lang="pt", dias=7)
    nots_us     = _fetch_noticias_raw("stock market NYSE Nasdaq Fed interest rates",  n=5, lang="en", dias=7)
    nots_global = _fetch_noticias_raw("global economy geopolitics oil trade",          n=4, lang="en", dias=7)

    def bloco_noticias(noticias, titulo, cor):
        html = f"<h3 style='color:{cor};margin-top:20px;'>{titulo}</h3>"
        for n in noticias:
            url  = n.get("url", "#")
            t    = n.get("title", "")
            fonte= n.get("source", {}).get("name", "")
            data = n.get("publishedAt", "")[:10]
            html += f"""<div style="background:#0e1318;border-left:3px solid {cor};padding:10px 14px;margin:6px 0;border-radius:6px;">
<a href="{url}" style="color:#e2e8f0;text-decoration:none;font-weight:600;font-size:0.92rem;">{t}</a>
<br><span style="color:#64748b;font-size:0.78rem;">{fonte} — {data}</span>
</div>"""
        return html

    corpo = f"""<html><body style="background:#080c10;color:#e2e8f0;font-family:Arial,sans-serif;padding:24px;max-width:700px;margin:auto;">
<h1 style="color:#00d4aa;border-bottom:2px solid #1a2332;padding-bottom:12px;">📈 MbInvest Bot Pro — Newsletter</h1>
<p style="color:#64748b;font-family:monospace;">{datetime.now().strftime("%d/%m/%Y %H:%M")}</p>

<div style="background:linear-gradient(135deg,#0a1628,#0d1f3c);border:1px solid #1a3a5c;border-radius:12px;padding:18px;margin:16px 0;">
<div style="color:#00d4aa;font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;">💬 Citação do Dia</div>
<p style="color:#e2e8f0;line-height:1.7;font-style:italic;font-size:1rem;margin:0 0 8px 0;">"{frase}"</p>
<p style="color:#0ea5e9;font-family:monospace;font-size:0.8rem;margin:0;">— {autor}</p>
</div>

<h2 style="color:#00d4aa;">🟢 Oportunidades de Compra</h2>
{"".join(bloco_ativo(*c) for c in compras[:5]) if compras else "<p style='color:#64748b;'>Nenhuma oportunidade de compra identificada hoje.</p>"}

<h2 style="color:#f43f5e;">🔴 Sinais de Venda / Cautela</h2>
{"".join(bloco_ativo(*v) for v in vendas[:4]) if vendas else "<p style='color:#64748b;'>Nenhum sinal de venda identificado hoje.</p>"}

<hr style="border-color:#1a2332;margin:24px 0;">
{bloco_noticias(nots_br,     "🇧🇷 Mercado Brasileiro", "#00d4aa")}
{bloco_noticias(nots_us,     "🇺🇸 Mercado Americano",  "#0ea5e9")}
{bloco_noticias(nots_global, "🌍 Geopolítica & Mundo", "#f59e0b")}

<p style="color:#64748b;font-size:0.75rem;margin-top:24px;text-align:center;">MbInvest Bot Pro · Este email é informativo e não constitui recomendação de investimento.</p>
</body></html>"""

    assunto = f"📈 MbInvest Bot Pro — {datetime.now().strftime('%d/%m')} · Oportunidades do Dia"
    subs    = carregar_subscribers()
    todos   = list(set(([GMAIL_USER] if GMAIL_USER else []) + subs))
    ok = True
    for email in todos:
        if not enviar_email(assunto, corpo, to=email):
            ok = False
    return ok


# ── Verificação de alertas de preço ──────────────────────────────────────────

def verificar_alertas():
    for alerta in st.session_state.alertas_preco:
        if not alerta.get("ativo", True):
            continue
        try:
            tk   = yf.Ticker(alerta["ticker"])
            hist = tk.history(period="1d", interval="5m")
            if hist.empty:
                continue
            preco_atual = hist["Close"].iloc[-1]
            disparar = (
                (alerta["tipo"] == "acima"  and preco_atual >= alerta["valor"]) or
                (alerta["tipo"] == "abaixo" and preco_atual <= alerta["valor"])
            )
            if disparar:
                alerta["ativo"] = False
                st.session_state.alertas_disparados.append({
                    **alerta,
                    "preco_disparado": preco_atual,
                    "hora": datetime.now().strftime("%d/%m %H:%M"),
                })
                sinal = "⬆️ subiu acima" if alerta["tipo"] == "acima" else "⬇️ caiu abaixo"
                corpo_alerta = f"""<html><body style="background:#080c10;color:#e2e8f0;font-family:Arial,sans-serif;padding:24px;max-width:600px;margin:auto;">
<h2 style="color:#f59e0b;">🔔 Alerta Disparado — MbInvest Bot Pro</h2>
<div style="background:#0e1318;border:1px solid #f59e0b;border-left:4px solid #f59e0b;border-radius:10px;padding:18px;margin:16px 0;">
<p style="font-size:1.1rem;"><b style="color:#0ea5e9;">{alerta['ticker']}</b> {sinal} de <b style="color:#f43f5e;">{alerta['valor']:.2f}</b></p>
<p>Preço atual: <b style="color:#00d4aa;font-size:1.2rem;">{preco_atual:.2f}</b></p>
<p style="color:#64748b;font-size:0.85rem;">Disparado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
</div>
<p style="color:#64748b;font-size:0.75rem;">MbInvest Bot Pro · Alerta automático de preço</p>
</body></html>"""
                dest = alerta.get("email", "") or GMAIL_USER
                if dest:
                    enviar_email(
                        f"🔔 Alerta MbInvest: {alerta['ticker']} atingiu {preco_atual:.2f}",
                        corpo_alerta, to=dest,
                    )
        except:
            pass


# ── Scheduler (thread daemon) ─────────────────────────────────────────────────

def rodar_scheduler():
    schedule.every().day.at("07:00").do(gerar_newsletter)
    schedule.every().day.at("13:00").do(gerar_newsletter)
    schedule.every().day.at("18:00").do(gerar_newsletter)
    schedule.every(5).minutes.do(verificar_alertas)
    while True:
        schedule.run_pending()
        time.sleep(60)
