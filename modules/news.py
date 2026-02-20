"""
news.py — Busca e renderização de notícias (NewsAPI).
Altere aqui: queries padrão, TTL do cache, número de artigos, filtros.
"""
import requests
import streamlit as st
from datetime import datetime, timedelta
from modules.config import NEWS_API_KEY


def _fetch_noticias_raw(query, n=8, lang="pt", dias=7):
    """Busca notícias sem cache — filtra pelos últimos `dias` dias."""
    if not NEWS_API_KEY:
        return []
    from_date = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    try:
        params = {
            "q":          query,
            "sortBy":     "publishedAt",
            "pageSize":   min(n, 20),
            "from":       from_date,
            "apiKey":     NEWS_API_KEY,
            "language":   lang,
        }
        arts = requests.get(
            "https://newsapi.org/v2/everything", params=params, timeout=10
        ).json().get("articles", [])
        if not arts and lang == "pt":
            params["language"] = "en"
            arts = requests.get(
                "https://newsapi.org/v2/everything", params=params, timeout=10
            ).json().get("articles", [])
        return [a for a in arts if a.get("title") and a.get("title") != "[Removed]"]
    except:
        return []


@st.cache_data(ttl=1800)
def buscar_noticias(query, n=8, lang="pt"):
    """Versão com cache de 30 min."""
    return _fetch_noticias_raw(query, n=n, lang=lang, dias=7)


@st.cache_data(ttl=1800)
def buscar_noticias_multi(queries_tuple, n_cada=5):
    """Busca notícias de múltiplas queries e deduplica."""
    vistas = set()
    resultado = []
    for q, lang in queries_tuple:
        for a in buscar_noticias(q, n=n_cada, lang=lang):
            titulo = a.get("title", "")
            if titulo and titulo not in vistas:
                vistas.add(titulo)
                resultado.append(a)
    resultado.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    return resultado


def render_noticias(lista, max_desc=220):
    """Renderiza cards de notícias com links clicáveis."""
    for n in lista:
        titulo  = n.get("title", "")
        fonte   = n.get("source", {}).get("name", "")
        data    = n.get("publishedAt", "")[:10]
        desc    = n.get("description", "") or ""
        url_n   = n.get("url", "#")
        urgente = any(p in titulo.lower() for p in [
            "urgente","breaking","alerta","crash","colapso","guerra","ataque","sanção"
        ])
        classe = "news-card news-urgent" if urgente else "news-card"
        badge  = (
            "<span style='background:#f59e0b;color:#000;font-size:0.65rem;"
            "padding:2px 6px;border-radius:4px;font-weight:700;margin-right:6px;'>"
            "🔴 URGENTE</span>"
        ) if urgente else ""
        st.markdown(f"""<div class='{classe}'>
{badge}<b><a href='{url_n}' target='_blank' style='color:#0ea5e9;text-decoration:none;font-size:0.95rem;'>{titulo}</a></b>
<br><span style='color:#64748b;font-size:0.78rem;'>📰 {fonte} · {data}</span>
<br><span style='color:#94a3b8;font-size:0.85rem;line-height:1.5;'>{desc[:max_desc]}{"..." if len(desc)>max_desc else ""}</span>
<br><a href='{url_n}' target='_blank' style='color:#00d4aa;font-size:0.78rem;text-decoration:none;'>→ Ler notícia completa</a>
</div>""", unsafe_allow_html=True)
