"""
app.py — Orquestrador principal do MbInvest Bot Pro.
Este arquivo contém apenas a UI (abas, sidebar, login).
Toda a lógica de negócio está nos módulos em modules/.

  modules/config.py      → credenciais, catálogos, índices, fundos
  modules/data.py        → busca e cálculo de indicadores (Yahoo Finance)
  modules/analysis.py    → score técnico e análise por IA (Claude)
  modules/news.py        → busca e renderização de notícias (NewsAPI)
  modules/charts.py      → gráficos Plotly (candlestick + indicadores)
  modules/email_utils.py → envio de email e gestão de subscribers
  modules/newsletter.py  → geração da newsletter + alertas + scheduler
  modules/styles.py      → CSS global e injeção de fontes
"""
import streamlit as st
import threading
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# ── Módulos internos ──────────────────────────────────────────────────────────
from modules.config import (
    CATALOGO, INDICES, FUNDOS,
    NEWS_API_KEY, ANTHROPIC_KEY, GMAIL_USER,
    APP_PASSWORD, MANUTENCAO, ADMIN_PASS,
)
from modules.data        import buscar_ativo
from modules.analysis    import gerar_analise, analisar_com_claude
from modules.news        import buscar_noticias, buscar_noticias_multi, render_noticias
from modules.charts      import plotar_grafico
from modules.email_utils import enviar_email, carregar_subscribers, salvar_subscribers, email_valido
from modules.newsletter  import gerar_newsletter, verificar_alertas, rodar_scheduler
from modules.styles      import CSS_BASE, inject_css

# ── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MbInvest Bot Pro", page_icon="📊", layout="wide")

# ─── Modo Manutenção ──────────────────────────────────────────────────────────
if MANUTENCAO:
    if "admin_ok" not in st.session_state: st.session_state.admin_ok = False
    if not st.session_state.admin_ok:
        st.markdown(CSS_BASE, unsafe_allow_html=True)
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>🔧 Em Manutenção</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-sub'>VOLTAMOS EM BREVE · MBINVEST BOT PRO</div>", unsafe_allow_html=True)
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
    st.markdown("<div class='login-title'>📈 MbInvest Bot Pro</div>", unsafe_allow_html=True)
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

# ─── CSS ──────────────────────────────────────────────────────────────────────
inject_css()

# ─── Session State ────────────────────────────────────────────────────────────
if "alertas_preco"      not in st.session_state: st.session_state.alertas_preco      = []
if "alertas_disparados" not in st.session_state: st.session_state.alertas_disparados = []
if "sched"              not in st.session_state: st.session_state.sched              = False
if "noticias_urgentes"  not in st.session_state: st.session_state.noticias_urgentes  = []
if "screener_res"       not in st.session_state: st.session_state.screener_res        = []
for _idx in range(5):
    if f"cat_res_{_idx}" not in st.session_state: st.session_state[f"cat_res_{_idx}"] = []
# Hot News — persiste categoria entre reruns
if "hot_q"    not in st.session_state: st.session_state.hot_q    = None
if "hot_lang" not in st.session_state: st.session_state.hot_lang = "pt"
if "hot_q_en" not in st.session_state: st.session_state.hot_q_en = None

# ─── Scheduler ────────────────────────────────────────────────────────────────
if not st.session_state.sched:
    st.session_state.sched = True
    threading.Thread(target=rodar_scheduler, daemon=True).start()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#00d4aa;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;'>MbInvest Bot Pro v3</div>", unsafe_allow_html=True)
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
st.markdown("<div class='header-main'>📈 MbInvest Bot Pro</div>", unsafe_allow_html=True)
st.markdown("<div class='header-sub'>MB INVESTIMENTOS · PLATAFORMA DE ANÁLISE · POWERED BY CLAUDE AI</div>", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom:20px'></div>", unsafe_allow_html=True)

abas = st.tabs([
    "🔍 Análise","📡 Screener","🔔 Alertas","📊 Índices",
    "🌍 Mundo","🔥 Hot News",
    "🇧🇷 B3","🇺🇸 EUA","₿ Cripto","🏢 FIIs","📊 ETFs",
    "💼 Fundos","💰 Renda Fixa","📧 Newsletter",
])

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

            # Alerta rápido
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
            tk_limpo  = ticker_inp.replace(".SA","").replace("-USD","")
            noticias  = buscar_noticias(f"{tk_limpo} {nome[:25]}", n=8)
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

    btn_col, clr_col = st.columns([4,1])
    with btn_col:
        iniciar_varredura = st.button("🚀 Iniciar Varredura", use_container_width=True)
    with clr_col:
        if st.button("🗑️ Limpar", use_container_width=True, key="clr_screener"):
            st.session_state.screener_res = []
            st.rerun()

    if iniciar_varredura:
        tks = list(dict.fromkeys([t for c in cats_sel for t in CATALOGO.get(c,[])]))
        res = []
        bar = st.progress(0)
        status_sc = st.empty()
        for i, tk in enumerate(tks):
            bar.progress((i+1)/len(tks))
            status_sc.markdown(f"<span style='color:#64748b;font-size:0.8rem;font-family:Space Mono,monospace;'>🔍 {tk} ({i+1}/{len(tks)})</span>", unsafe_allow_html=True)
            try:
                df, info = buscar_ativo(tk, periodo_sc)
                if df is not None:
                    score,pros,contras,alertas,rec,var,var1d,alvo_a,alvo_b = gerar_analise(df, tk)
                    if score >= min_score:
                        res.append({"Ticker":tk,"Score":score,"Recomendação":rec,"Var%":round(var,2),"Var1D%":round(var1d,2),
                                    "RSI":round(df["RSI"].iloc[-1],1),"MACD":round(df["MACD"].iloc[-1],4),
                                    "Alertas":len(alertas),"_df":df,"_info":info,"_pros":pros,"_contras":contras,
                                    "_alvo_a":alvo_a,"_alvo_b":alvo_b})
            except: pass
        bar.empty(); status_sc.empty()
        res.sort(key=lambda x: x["Score"], reverse=True)
        st.session_state.screener_res = res
        if not res:
            st.warning("Nenhum ativo acima do score mínimo.")

    if st.session_state.screener_res:
        cols_show = ["Ticker","Score","Recomendação","Var%","Var1D%","RSI","Alertas"]
        df_sc = pd.DataFrame([{k:v for k,v in r.items() if not k.startswith("_")} for r in st.session_state.screener_res])
        st.dataframe(df_sc, use_container_width=True, hide_index=True)
        st.markdown("---")
        st.markdown("#### 🔍 Detalhes por Ativo")
        for row in st.session_state.screener_res:
            cor = "#00d4aa" if "COMPRA" in row["Recomendação"] else ("#f59e0b" if "NEUTRO" in row["Recomendação"] else "#f43f5e")
            with st.expander(f"{row['Ticker']} | Score {row['Score']}/100 | {row['Recomendação']} | Var {row['Var%']:+.1f}%"):
                g1,g2 = st.columns([3,1])
                with g1: st.plotly_chart(plotar_grafico(row["_df"], row["Ticker"]), use_container_width=True, key=f"sc_chart_{row['Ticker']}")
                with g2:
                    st.markdown(f"<div style='background:{cor}15;border:1px solid {cor};border-radius:8px;padding:12px;'><b style='color:{cor};font-size:1.05rem;'>{row['Recomendação']}</b><br><span style='color:#64748b;'>Score: {row['Score']}/100</span></div>", unsafe_allow_html=True)
                    st.markdown(f"**RSI:** {row['RSI']}")
                    if row["_alvo_a"]: st.markdown(f"🎯 **Alvo:** {row['_alvo_a']:.2f}")
                    if row["_alvo_b"]: st.markdown(f"🛡️ **Stop:** {row['_alvo_b']:.2f}")
                    tb,tc = st.tabs(["✅ Prós","❌ Contras"])
                    with tb:
                        for p in row["_pros"]: st.write(p)
                    with tc:
                        for c_ in row["_contras"]: st.write(c_)
                if usar_ia_sc and ANTHROPIC_KEY:
                    st.markdown("---")
                    st.markdown("#### 🤖 Análise IA")
                    with st.spinner("Claude analisando..."):
                        ai_txt, ai_err = analisar_com_claude(row["Ticker"], row["_df"], row["_info"], row["Score"], row["_pros"], row["_contras"], row["Recomendação"], row["Var%"], row["Var1D%"], row["_alvo_a"], row["_alvo_b"])
                    if ai_err: st.error(ai_err)
                    else: st.markdown(f"<div class='ai-card'><div class='ai-label'>⚡ Claude AI</div><div class='ai-text'>{ai_txt.replace(chr(10),'<br>')}</div></div>", unsafe_allow_html=True)

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
        fa4,fa5 = st.columns([3,1])
        with fa4: al_email = st.text_input("E-mail para notificação:", placeholder="seu@email.com (deixe vazio para usar o email admin)")
        with fa5:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            al_verificar = st.form_submit_button("🔍 Verificar preço atual", use_container_width=True)
        if st.form_submit_button("➕ Adicionar Alerta", use_container_width=True):
            if al_ticker.strip():
                email_dest = al_email.strip().lower() if al_email.strip() else ""
                st.session_state.alertas_preco.append({
                    "ticker": al_ticker.strip().upper(),
                    "tipo":   al_tipo,
                    "valor":  al_valor,
                    "email":  email_dest,
                    "ativo":  True,
                    "criado": datetime.now().strftime("%d/%m %H:%M"),
                })
                dest_txt = f" · Email: {email_dest}" if email_dest else " · Email: admin"
                st.success(f"✅ Alerta criado para {al_ticker.upper()}{dest_txt}")
            else:
                st.error("Informe o ticker!")
        if al_verificar and al_ticker.strip():
            import yfinance as yf
            with st.spinner(f"Buscando preço de {al_ticker.upper()}..."):
                try:
                    tk_v = yf.Ticker(al_ticker.strip().upper())
                    h_v  = tk_v.history(period="1d", interval="5m")
                    if not h_v.empty:
                        p_v = h_v["Close"].iloc[-1]
                        st.info(f"💰 Preço atual de **{al_ticker.upper()}**: **{p_v:.2f}**")
                    else:
                        st.warning("Ativo não encontrado.")
                except:
                    st.error("Erro ao buscar preço.")

    st.markdown("---")
    ativos = [a for a in st.session_state.alertas_preco if a.get("ativo",True)]
    if ativos:
        st.markdown(f"#### 🟢 Alertas Ativos ({len(ativos)})")
        for i, alerta in enumerate(st.session_state.alertas_preco):
            if not alerta.get("ativo",True): continue
            c1,c2,c3,c4,c5,c6 = st.columns([2,1,1,2,1,1])
            c1.markdown(f"<span style='font-family:Space Mono,monospace;color:#0ea5e9;'>📊 {alerta['ticker']}</span>", unsafe_allow_html=True)
            c2.markdown(f"<span style='color:#64748b;font-size:0.82rem;'>{alerta['tipo']}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='font-family:Space Mono,monospace;color:#f59e0b;'>{alerta['valor']:.2f}</span>", unsafe_allow_html=True)
            email_show = alerta.get('email','') or 'admin'
            c4.markdown(f"<span style='color:#64748b;font-size:0.72rem;font-family:Space Mono,monospace;'>✉️ {email_show}</span>", unsafe_allow_html=True)
            c5.markdown(f"<span style='color:#64748b;font-size:0.72rem;'>{alerta['criado']}</span>", unsafe_allow_html=True)
            if c6.button("🗑️", key=f"del_{i}"):
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
    import yfinance as yf
    st.markdown("### 📊 Índices & Mercados Globais")
    col_ref, col_esp = st.columns([1,4])
    with col_ref:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()

    cols = st.columns(4)
    for i, (nome_idx, ticker_idx, regiao) in enumerate(INDICES):
        with cols[i%4]:
            try:
                tk   = yf.Ticker(ticker_idx)
                hist = tk.history(period="5d")
                if not hist.empty and len(hist) >= 2:
                    preco_at  = hist["Close"].iloc[-1]
                    preco_ant = hist["Close"].iloc[-2]
                    variacao  = ((preco_at - preco_ant) / preco_ant) * 100
                    cor_var   = "indice-var-pos" if variacao >= 0 else "indice-var-neg"
                    sinal     = "▲" if variacao >= 0 else "▼"
                    val_fmt   = f"{preco_at:,.0f}" if preco_at > 1000 else (f"{preco_at:,.2f}" if preco_at > 10 else f"{preco_at:,.4f}")
                    st.markdown(f"""<div class='indice-card' style='margin-bottom:12px;'>
<div class='indice-nome'>{regiao} · {nome_idx}</div>
<div class='indice-valor'>{val_fmt}</div>
<div class='{cor_var}'>{sinal} {abs(variacao):.2f}%</div>
</div>""", unsafe_allow_html=True)
            except:
                st.markdown(f"<div class='indice-card' style='margin-bottom:12px;'><div class='indice-nome'>{nome_idx}</div><div style='color:#64748b;font-size:0.8rem;'>Indisponível</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    tab_ind, tab_comp = st.tabs(["📈 Gráfico Individual", "📊 Comparar Índices"])

    with tab_ind:
        idx_sel = st.selectbox("Selecionar índice:", [n for n,_,_ in INDICES], key="idx_ind")
        ticker_idx_sel = next((t for n,t,_ in INDICES if n==idx_sel), "^BVSP")
        periodo_idx = st.selectbox("Período:", ["1mo","3mo","6mo","1y","2y"], key="p_idx")
        df_idx, _ = buscar_ativo(ticker_idx_sel, periodo_idx)
        if df_idx is not None:
            st.plotly_chart(plotar_grafico(df_idx, idx_sel), use_container_width=True)
        else:
            st.warning("Dados indisponíveis para este índice no momento.")

    with tab_comp:
        st.markdown("#### 📊 Comparativo de Desempenho (base 100)")
        st.markdown("<p style='color:#64748b;font-size:0.85rem;'>Todos os índices normalizados para 100 — compare o desempenho relativo.</p>", unsafe_allow_html=True)
        nomes_idx  = [n for n,_,_ in INDICES]
        comp_sel   = st.multiselect("Selecionar índices:", nomes_idx, default=["Ibovespa","S&P 500","Bitcoin","Ouro","Dólar/BRL"])
        periodo_comp = st.selectbox("Período:", ["1mo","3mo","6mo","1y","2y"], key="p_comp")
        if comp_sel and st.button("📊 Comparar", use_container_width=True):
            fig_comp    = go.Figure()
            cores_comp  = ["#00d4aa","#0ea5e9","#f59e0b","#a78bfa","#f43f5e","#34d399","#fb923c","#60a5fa"]
            dados_ok    = 0
            prog_comp   = st.progress(0)
            for ci, nome_c in enumerate(comp_sel):
                prog_comp.progress((ci+1)/len(comp_sel))
                ticker_c = next((t for n,t,_ in INDICES if n==nome_c), None)
                if not ticker_c: continue
                try:
                    tk_c  = yf.Ticker(ticker_c)
                    h_c   = tk_c.history(period=periodo_comp)
                    if h_c.empty or len(h_c) < 2: continue
                    h_c.index = h_c.index.tz_localize(None) if h_c.index.tz else h_c.index
                    datas_c = [str(d)[:10] for d in h_c.index]
                    base    = h_c["Close"].iloc[0]
                    norm    = (h_c["Close"] / base * 100).tolist()
                    cor_c   = cores_comp[dados_ok % len(cores_comp)]
                    fig_comp.add_trace(go.Scatter(x=datas_c, y=norm, name=nome_c, line=dict(color=cor_c, width=2), mode="lines"))
                    dados_ok += 1
                except: pass
            prog_comp.empty()
            if dados_ok:
                fig_comp.add_hline(y=100, line_dash="dot", line_color="#64748b", opacity=0.5)
                fig_comp.update_layout(
                    template="plotly_dark", height=500,
                    paper_bgcolor="#080c10", plot_bgcolor="#080c10",
                    legend=dict(orientation="h", x=0, y=1.08, font=dict(size=10, color="#e2e8f0"), bgcolor="rgba(0,0,0,0)"),
                    margin=dict(l=60,r=20,t=80,b=40), font=dict(color="#e2e8f0"),
                    yaxis=dict(gridcolor="#1a2332", ticksuffix=" pts", title="Desempenho (base 100)"),
                    xaxis=dict(gridcolor="#1a2332"),
                )
                st.plotly_chart(fig_comp, use_container_width=True)
                st.markdown("<p style='color:#64748b;font-size:0.78rem;font-family:Space Mono,monospace;'>Base 100 = primeiro dia do período. Acima de 100 = valorização.</p>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ABA 4 — MUNDO (PORTAL GEOPOLÍTICO)
# ═══════════════════════════════════════════════════════════════════
with abas[4]:
    st.markdown("### 🌍 Portal Mundial — Geopolítica & Economia Global")

    regioes = {
        "🇧🇷 Brasil":     [("bolsa B3 Ibovespa economia Brasil mercado","pt"), ("Brazil Ibovespa B3 Bovespa stock exchange economy","en")],
        "🇺🇸 EUA":        [("US economy Fed interest rates stock market","en"), ("Wall Street Nasdaq NYSE","en")],
        "🇪🇺 Europa":     [("Europe economy ECB inflation eurozone","en"), ("European markets DAX FTSE","en")],
        "🇨🇳 China":      [("China economy trade yuan market","en"), ("China GDP property market","en")],
        "🌍 Geopolítica": [("geopolitics war sanctions trade conflict","en"), ("BRICS NATO G7 global economy","en")],
        "🛢️ Commodities": [("oil gold silver commodity prices","en"), ("petróleo ouro commodities mercado","pt")],
        "₿ Cripto Global":[("bitcoin ethereum crypto regulation blockchain","en"), ("cripto bitcoin ethereum mercado","pt")],
        "📰 Tudo":        [("global economy finance markets","en"), ("mercado financeiro mundial economia","pt"), ("Asia Pacific markets economy","en"), ("Middle East economy oil","en")],
    }

    regiao_sel = st.radio("Região:", list(regioes.keys()), horizontal=True)

    col_atualizar, col_info = st.columns([1,4])
    with col_atualizar:
        if st.button("🔄 Atualizar", key="btn_refresh_mundo"):
            buscar_noticias_multi.clear()
            buscar_noticias.clear()
            st.rerun()
    with col_info:
        st.markdown(f"<span style='color:#64748b;font-size:0.78rem;font-family:Space Mono,monospace;'>🕐 Cache 30 min · última busca: {datetime.now().strftime('%H:%M')}</span>", unsafe_allow_html=True)

    with st.spinner("Buscando notícias do mundo..."):
        queries = regioes[regiao_sel]
        noticias_mundo = buscar_noticias_multi(tuple(queries), n_cada=8)

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
    if c1.button("🇧🇷 Brasil",  use_container_width=True):
        st.session_state.hot_q="bolsa B3 Ibovespa economia Brasil"; st.session_state.hot_lang="pt"; st.session_state.hot_q_en="Brazil Ibovespa B3 Bovespa stock market economy"
    if c2.button("🌎 Global",   use_container_width=True):
        st.session_state.hot_q="stock market economy Fed interest rates"; st.session_state.hot_lang="en"; st.session_state.hot_q_en=None
    if c3.button("₿ Cripto",    use_container_width=True):
        st.session_state.hot_q="bitcoin ethereum crypto blockchain"; st.session_state.hot_lang="en"; st.session_state.hot_q_en=None
    if c4.button("📰 Tudo",     use_container_width=True):
        st.session_state.hot_q="mercado financeiro bolsa bitcoin economia mundo"; st.session_state.hot_lang="pt"; st.session_state.hot_q_en=None

    q_hot    = st.session_state.hot_q
    lang_hot = st.session_state.hot_lang
    q_hot_en = st.session_state.hot_q_en

    if q_hot:
        col_r, col_t = st.columns([1,5])
        with col_r:
            if st.button("🔄 Atualizar", key="btn_refresh_hot"):
                buscar_noticias.clear(); buscar_noticias_multi.clear(); st.rerun()
        with col_t:
            st.markdown(f"<span style='color:#64748b;font-size:0.78rem;font-family:Space Mono,monospace;'>🕐 Cache 30 min · {datetime.now().strftime('%H:%M')}</span>", unsafe_allow_html=True)
        with st.spinner("Buscando..."):
            nots = buscar_noticias(q_hot, n=18, lang=lang_hot)
            if not nots and lang_hot == "pt":
                q_fb = q_hot_en if q_hot_en else q_hot
                nots = buscar_noticias(q_fb, n=18, lang="en")
        if nots: render_noticias(nots, max_desc=250)
        elif not NEWS_API_KEY: st.info("Configure NEWS_API_KEY no .env.")
        else: st.warning("Nenhuma notícia encontrada no momento. Tente clicar em 🔄 Atualizar.")
    else:
        st.markdown("<div style='text-align:center;padding:60px;color:#64748b;'><h2 style='font-family:Space Mono,monospace;'>→ Escolha uma categoria acima</h2></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ABAS 6-10 — CATEGORIAS (B3, EUA, Cripto, FIIs, ETFs)
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

        btn_c, clr_c = st.columns([4,1])
        with btn_c:
            carregar_cat = st.button(f"🔎 Carregar {nome_aba}", key=f"btn_{aba_idx}", use_container_width=True)
        with clr_c:
            if st.button("🗑️", key=f"clr_{aba_idx}", use_container_width=True):
                st.session_state[f"cat_res_{aba_idx}"] = []
                st.rerun()

        if carregar_cat:
            res_cat = []
            bar2 = st.progress(0)
            status2 = st.empty()
            for i,tk in enumerate(tks_cat):
                bar2.progress((i+1)/len(tks_cat))
                status2.markdown(f"<span style='color:#64748b;font-size:0.8rem;font-family:Space Mono,monospace;'>🔍 {tk} ({i+1}/{len(tks_cat)})</span>", unsafe_allow_html=True)
                try:
                    df,info = buscar_ativo(tk, p_cat)
                    if df is not None:
                        score,pros,contras,alertas,rec,var,var1d,alvo_a,alvo_b = gerar_analise(df,tk)
                        res_cat.append((tk,df,info,score,pros,contras,alertas,rec,var,var1d,alvo_a,alvo_b))
                except: pass
            bar2.empty(); status2.empty()
            res_cat.sort(key=lambda x:x[3],reverse=True)
            st.session_state[f"cat_res_{aba_idx}"] = res_cat
            if not res_cat:
                st.warning("Nenhum dado disponível no momento. Tente novamente.")

        for tk,df,info,score,pros,contras,alertas,rec,var,var1d,alvo_a,alvo_b in st.session_state[f"cat_res_{aba_idx}"]:
            cor = "#00d4aa" if "COMPRA" in rec else ("#f59e0b" if "NEUTRO" in rec else "#f43f5e")
            preco_atual = df['Close'].iloc[-1]
            with st.expander(f"{tk} | {preco_atual:.2f} | {var:+.1f}% | Score {score}/100 | {rec}"):
                for a in alertas: st.warning(a)
                g1,g2 = st.columns([3,1])
                with g1: st.plotly_chart(plotar_grafico(df,tk), use_container_width=True, key=f"chart_{tk}_{aba_idx}")
                with g2:
                    st.markdown(f"<div style='background:{cor}15;border:1px solid {cor};border-radius:8px;padding:12px;'><b style='color:{cor};font-size:1.05rem;'>{rec}</b><br><span style='color:#64748b;'>Score: {score}/100</span></div>", unsafe_allow_html=True)
                    st.markdown(f"**RSI:** {df['RSI'].iloc[-1]:.1f}")
                    if alvo_a: st.markdown(f"🎯 **Alvo:** {alvo_a:.2f}")
                    if alvo_b: st.markdown(f"🛡️ **Stop:** {alvo_b:.2f}")
                    with st.form(key=f"form_{tk}_{aba_idx}"):
                        val_f = st.number_input("Alerta acima de:", value=round(preco_atual*1.05,2), step=0.01)
                        em_f  = st.text_input("Email:", placeholder="seu@email.com", key=f"em_{tk}_{aba_idx}")
                        if st.form_submit_button("🔔 Criar Alerta"):
                            st.session_state.alertas_preco.append({"ticker":tk,"tipo":"acima","valor":val_f,"email":em_f.strip(),"ativo":True,"criado":datetime.now().strftime("%d/%m %H:%M")})
                            st.success("✅ Alerta criado!")
                    tp,tc = st.tabs(["✅ Prós","❌ Contras"])
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
        "Rentab.":  ["~15.0%","IPCA+7.5%","~15.0%","~18.0%","~13.5%","~13.8%","IPCA+7%","IPCA+8%"],
        "IR":       ["Sim","Sim","Sim","Sim","Isento","Isento","Sim/Isento","Isento"],
        "Liquidez": ["Diária","Vencto","Vencto","Vencto","Vencto","Vencto","Vencto","Vencto"],
        "FGC":      ["Não","Não","Sim","Sim","Sim","Sim","Não","Não"],
        "Score":    [90,87,78,88,76,77,85,88],
    }).sort_values("Score",ascending=False)
    st.dataframe(df_rf, use_container_width=True, hide_index=True)

    r1,r2,r3,r4 = st.columns(4)
    with r1: valor=st.number_input("Capital (R$):",value=10000,step=1000)
    with r2: taxa=st.number_input("Taxa anual (%):",value=15.0,step=0.25)
    with r3: meses=st.slider("Prazo (meses):",1,120,12)
    with r4: ir_op=st.selectbox("IR:",["Sim","Isento"])
    taxa_m  = (1+taxa/100)**(1/12)-1
    meses_r = list(range(1,meses+1))
    valores = [valor*(1+taxa_m)**m for m in meses_r]
    rend    = valores[-1]-valor
    aliq    = 0.225 if meses<=6 else (0.20 if meses<=12 else (0.175 if meses<=24 else 0.15)) if ir_op=="Sim" else 0
    fig_rf  = go.Figure()
    fig_rf.add_trace(go.Scatter(x=meses_r,y=valores,fill="tozeroy",line=dict(color="#00d4aa",width=2),name="Patrimônio"))
    fig_rf.update_layout(template="plotly_dark",height=280,paper_bgcolor="#080c10",plot_bgcolor="#080c10",margin=dict(l=40,r=20,t=20,b=40))
    st.plotly_chart(fig_rf,use_container_width=True)
    s1,s2,s3=st.columns(3)
    s1.metric("Patrimônio Bruto",    f"R$ {valores[-1]:,.2f}")
    s2.metric("Rendimento Líquido",  f"R$ {rend*(1-aliq):,.2f}")
    s3.metric("IR Pago",             f"R$ {rend*aliq:,.2f}" if aliq>0 else "Isento")

# ═══════════════════════════════════════════════════════════════════
# ABA 13 — NEWSLETTER
# ═══════════════════════════════════════════════════════════════════
with abas[13]:
    st.markdown("### 📧 Newsletter MbInvest Bot Pro")

    # ── Inscrição ─────────────────────────────────────────────────
    st.markdown("#### ✉️ Receba a newsletter no seu e-mail")
    st.markdown("<p style='color:#64748b;font-size:0.88rem;'>Análises diárias de mercado, oportunidades de compra e venda e notícias globais — direto no seu e-mail às <b>07h, 13h e 18h</b>.</p>", unsafe_allow_html=True)

    with st.form("form_inscricao"):
        col_e, col_b = st.columns([3,1])
        with col_e:
            novo_email = st.text_input("", placeholder="seu@email.com", label_visibility="collapsed")
        with col_b:
            inscrever = st.form_submit_button("📩 Inscrever", use_container_width=True)
        if inscrever:
            novo_email = novo_email.strip().lower()
            if not email_valido(novo_email):
                st.error("❌ E-mail inválido. Verifique o formato.")
            else:
                subs = carregar_subscribers()
                if novo_email in subs:
                    st.warning("⚠️ Este e-mail já está inscrito.")
                else:
                    subs.append(novo_email)
                    salvar_subscribers(subs)
                    corpo_bvs = f"""<html><body style="background:#080c10;color:#e2e8f0;font-family:Arial,sans-serif;padding:24px;max-width:600px;margin:auto;">
<h2 style="color:#00d4aa;">📈 Bem-vindo ao MbInvest Bot Pro!</h2>
<p>Seu e-mail <b>{novo_email}</b> foi cadastrado com sucesso.</p>
<p style="color:#64748b;">Você receberá análises de mercado todos os dias às 07h, 13h e 18h.</p>
<p style="color:#64748b;font-size:0.8rem;margin-top:24px;">Para cancelar, entre em contato com o administrador.</p>
</body></html>"""
                    enviar_email("✅ Inscrição confirmada — MbInvest Bot Pro", corpo_bvs, to=novo_email)
                    st.success("✅ Inscrito! Você receberá um e-mail de confirmação em breve.")

    st.markdown("---")
    st.markdown("""
**A newsletter inclui:**
- 🟢 **Oportunidades de Compra** identificadas pela análise técnica
- 🔴 **Sinais de Venda / Cautela**
- 💬 **Citação do Dia** de grandes investidores e pensadores econômicos
- 🇧🇷 Notícias do Mercado Brasileiro
- 🇺🇸 Notícias do Mercado Americano
- 🌍 Geopolítica & Mundo
""")

    st.markdown("---")
    st.markdown("#### ⏰ Próximos Envios")
    agora = datetime.now()
    for hora in ["07:00","13:00","18:00"]:
        h,m_ = map(int, hora.split(":"))
        prox  = agora.replace(hour=h, minute=m_, second=0)
        if prox < agora: prox += timedelta(days=1)
        diff  = prox - agora
        hr    = int(diff.seconds//3600)
        mn    = int((diff.seconds%3600)//60)
        st.markdown(f"<span style='font-family:Space Mono,monospace;color:#64748b;'>🕐 **{hora}** — em {hr}h {mn}min</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🔐 Painel Administrativo")
    if "admin_nl" not in st.session_state: st.session_state.admin_nl = False
    if not st.session_state.admin_nl:
        with st.form("form_admin_nl"):
            adm_s = st.text_input("Senha admin:", type="password", label_visibility="collapsed", placeholder="Senha de administrador")
            if st.form_submit_button("🔓 Acessar painel", use_container_width=True):
                if adm_s == ADMIN_PASS:
                    st.session_state.admin_nl = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta.")
    else:
        subs = carregar_subscribers()
        st.markdown(f"<div style='background:#0ea5e915;border:1px solid #0ea5e9;border-radius:8px;padding:12px;margin-bottom:12px;'><b style='color:#0ea5e9;'>👥 {len(subs)} inscritos</b></div>", unsafe_allow_html=True)

        na1, na2 = st.columns(2)
        with na1:
            if st.button("📤 Enviar Newsletter Agora", use_container_width=True):
                with st.spinner("Analisando mercado e montando newsletter..."):
                    ok = gerar_newsletter()
                total = len(subs) + (1 if GMAIL_USER else 0)
                if ok: st.success(f"✅ Enviado para {total} destinatário(s)!")
                else:  st.error("❌ Erro no envio. Verifique as credenciais.")
        with na2:
            if st.button("🧪 Testar Conexão Gmail", use_container_width=True):
                ok = enviar_email("✅ Teste MbInvest","<h2 style='color:#00d4aa;'>Funcionando! 🚀</h2>")
                if ok: st.success("✅ Gmail conectado!")
                else:  st.error("❌ Falha — verifique GMAIL_USER e GMAIL_PASS")

        if subs:
            st.markdown("##### 📋 Lista de Inscritos")
            for i, email_s in enumerate(subs):
                ca, cb = st.columns([4,1])
                ca.markdown(f"<span style='font-family:Space Mono,monospace;color:#e2e8f0;font-size:0.88rem;'>{email_s}</span>", unsafe_allow_html=True)
                if cb.button("🗑️", key=f"rem_{i}"):
                    subs.pop(i)
                    salvar_subscribers(subs)
                    st.rerun()
        else:
            st.info("Nenhum inscrito ainda.")

        if st.button("🔒 Sair do painel admin"):
            st.session_state.admin_nl = False
            st.rerun()
