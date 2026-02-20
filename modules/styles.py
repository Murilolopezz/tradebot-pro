"""
styles.py — CSS global e injeção de fontes.
Altere aqui: cores do tema, fontes, estilos de cards, botões, tabs.
"""
import streamlit as st

CSS_BASE = """<style>
html,body,.stApp{background:#080c10!important;}
.login-box{max-width:380px;margin:80px auto;background:#0e1318;border:1px solid #1a2332;border-radius:16px;padding:40px;text-align:center;}
.login-title{font-family:'Syne',sans-serif;font-size:1.9rem;font-weight:800;background:linear-gradient(135deg,#00d4aa,#0ea5e9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px;}
.login-sub{color:#64748b;font-family:Space Mono,monospace;font-size:0.75rem;letter-spacing:1px;margin-bottom:28px;}
</style>"""


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

/* ── Inputs ──────────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
}
.stTextInput input:focus, .stTextInput input:active,
.stNumberInput input:focus, .stNumberInput input:active {
    background: var(--surface) !important; color: var(--text) !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(0,212,170,0.2) !important; outline: none !important;
}
.stTextInput input::placeholder, .stNumberInput input::placeholder { color: var(--muted) !important; }

/* ── Selectbox ───────────────────────────────────────────────── */
div[data-baseweb="select"] > div { background: var(--surface) !important; border-color: var(--border) !important; color: var(--text) !important; }
div[data-baseweb="select"] > div:hover { border-color: var(--accent) !important; }
div[data-baseweb="select"] span { color: var(--text) !important; }
[data-baseweb="popover"], [data-baseweb="menu"] {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: 10px !important; box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
}
[data-baseweb="option"] { background: var(--surface) !important; color: var(--text) !important; }
[data-baseweb="option"]:hover { background: #1a2332 !important; color: var(--accent) !important; }
[data-baseweb="option"][aria-selected="true"] { background: rgba(0,212,170,0.12) !important; color: var(--accent) !important; }
li[role="option"] { background: var(--surface) !important; color: var(--text) !important; }
li[role="option"]:hover { background: #1a2332 !important; }

/* ── Botões ──────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #000 !important; border: none !important; border-radius: 8px !important;
    font-weight: 700 !important; font-family: 'Syne', sans-serif !important; transition: all 0.2s ease;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,212,170,0.3); background: linear-gradient(135deg, var(--accent), var(--accent2)) !important; color: #000 !important; }
.stButton > button:active, .stButton > button:focus { background: linear-gradient(135deg, var(--accent), var(--accent2)) !important; color: #000 !important; box-shadow: 0 0 0 3px rgba(0,212,170,0.35) !important; outline: none !important; }

/* Botão form submit */
.stFormSubmitButton > button { background: linear-gradient(135deg, var(--accent), var(--accent2)) !important; color: #000 !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; }
.stFormSubmitButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,212,170,0.3); background: linear-gradient(135deg, var(--accent), var(--accent2)) !important; color: #000 !important; }
.stFormSubmitButton > button:active, .stFormSubmitButton > button:focus { background: linear-gradient(135deg, var(--accent), var(--accent2)) !important; color: #000 !important; outline: none !important; }

/* ── Multiselect ─────────────────────────────────────────────── */
[data-baseweb="tag"] { background: rgba(0,212,170,0.15) !important; border: 1px solid var(--accent) !important; color: var(--accent) !important; border-radius: 6px !important; }
[data-baseweb="tag"] span { color: var(--accent) !important; }
[data-baseweb="tag"] button { color: var(--accent) !important; }

/* ── Radio / Checkbox ────────────────────────────────────────── */
.stRadio label, .stCheckbox label { color: var(--text) !important; }
.stRadio [data-testid="stWidgetLabel"], .stCheckbox [data-testid="stWidgetLabel"] { color: var(--text) !important; }
.stCheckbox input:checked ~ div, .stCheckbox input:checked + div { background-color: var(--accent) !important; border-color: var(--accent) !important; }

/* ── Tabs internas ───────────────────────────────────────────── */
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) { background: rgba(0,212,170,0.06) !important; color: var(--text) !important; }
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; }

/* ── Expander ────────────────────────────────────────────────── */
[data-testid="stExpander"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; overflow: hidden; }
[data-testid="stExpander"] > details > summary { color: var(--text) !important; background: var(--surface) !important; }
[data-testid="stExpander"] > details > summary:hover { background: rgba(0,212,170,0.05) !important; color: var(--text) !important; }
[data-testid="stExpander"] > details[open] > summary { border-color: var(--accent) !important; }
[data-testid="stExpander"] > details > div { background: var(--surface) !important; }

/* ── Forms ───────────────────────────────────────────────────── */
[data-testid="stForm"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; }

/* ── Slider ──────────────────────────────────────────────────── */
[data-baseweb="slider"] [role="slider"] { background: var(--accent) !important; border: 2px solid var(--accent) !important; }
[data-baseweb="slider"] div[data-testid*="thumb"] { background: var(--accent) !important; }

/* ── Number input spinner ────────────────────────────────────── */
.stNumberInput button { background: var(--surface) !important; color: var(--text) !important; border-color: var(--border) !important; }
.stNumberInput button:hover { background: #1a2332 !important; color: var(--accent) !important; }

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

/* ── Cards de notícias ───────────────────────────────────────── */
.news-card { background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--accent2); border-radius: 10px; padding: 14px; margin: 6px 0; transition: border-color 0.2s, transform 0.2s; }
.news-card:hover { border-color: var(--accent); transform: translateX(3px); }
.news-urgent { background: linear-gradient(135deg, #f59e0b08, #f59e0b18); border: 1px solid var(--warn) !important; border-left: 4px solid var(--warn) !important; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(245,158,11,0.3)} 50%{box-shadow:0 0 12px 4px rgba(245,158,11,0.15)} }

/* ── Sinais de trade ─────────────────────────────────────────── */
.signal-buy     { background: linear-gradient(135deg, #00d4aa08, #00d4aa15); border: 1px solid var(--buy);     border-radius: 12px; padding: 16px; }
.signal-sell    { background: linear-gradient(135deg, #f43f5e08, #f43f5e15); border: 1px solid var(--sell);    border-radius: 12px; padding: 16px; }
.signal-neutral { background: linear-gradient(135deg, #f59e0b08, #f59e0b15); border: 1px solid var(--neutral); border-radius: 12px; padding: 16px; }

/* ── Card IA ─────────────────────────────────────────────────── */
.ai-card { background: linear-gradient(135deg, #0a1628, #0d1f3c); border: 1px solid #1a3a5c; border-radius: 14px; padding: 20px; margin-top: 12px; position: relative; overflow: hidden; }
.ai-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background: linear-gradient(90deg, var(--accent), var(--accent2), var(--accent)); }
.ai-label { font-family:'Space Mono',monospace; font-size:0.7rem; color:var(--accent); text-transform:uppercase; letter-spacing:2px; margin-bottom:8px; }
.ai-text { color:var(--text); line-height:1.7; font-size:0.92rem; }

/* ── Cards de índices ────────────────────────────────────────── */
.indice-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; transition: border-color 0.2s, transform 0.2s; }
.indice-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.indice-nome { font-family:'Space Mono',monospace; font-size:0.75rem; color:var(--muted); text-transform:uppercase; letter-spacing:1px; }
.indice-valor { font-family:'Space Mono',monospace; font-size:1.4rem; font-weight:700; color:var(--text); margin:4px 0; }
.indice-var-pos { color: var(--buy); font-weight:700; font-family:'Space Mono',monospace; font-size:0.9rem; }
.indice-var-neg { color: var(--sell); font-weight:700; font-family:'Space Mono',monospace; font-size:0.9rem; }

/* ── Header ──────────────────────────────────────────────────── */
.header-main { font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800; background:linear-gradient(135deg,var(--accent),var(--accent2)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; letter-spacing:-1px; margin-bottom:2px; }
.header-sub { color:var(--muted); font-size:0.85rem; font-family:'Space Mono',monospace; letter-spacing:1px; }

div[data-testid="stAlert"] { border-radius:8px !important; border-left-width:3px !important; }
div.stSlider > div { padding-top:4px; }
</style>""", unsafe_allow_html=True)

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
