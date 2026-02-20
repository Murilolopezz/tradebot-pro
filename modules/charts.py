"""
charts.py — Geração de gráficos Plotly (candlestick + indicadores).
Altere aqui: cores, layout, indicadores exibidos no gráfico.
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plotar_grafico(df, ticker):
    datas = [str(d)[:10] for d in df.index]
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.55, 0.15, 0.15, 0.15],
        subplot_titles=(f"{ticker}", "Volume", "RSI (14)", "MACD"),
    )

    # ── Candlestick ──────────────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=datas, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Preço",
        increasing_line_color="#00d4aa", decreasing_line_color="#f43f5e",
        increasing_fillcolor="#00d4aa",  decreasing_fillcolor="#f43f5e",
    ), row=1, col=1)

    # ── Médias móveis ────────────────────────────────────────────────────────
    for col, color, dash in [
        ("SMA20",  "#FFD700", "solid"),
        ("SMA50",  "#FF8C00", "solid"),
        ("SMA200", "#f43f5e", "dash"),
        ("EMA9",   "#00d4aa", "dot"),
        ("EMA21",  "#0ea5e9", "dot"),
    ]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=datas, y=df[col], name=col,
                line=dict(color=color, width=1.3, dash=dash), opacity=0.85,
            ), row=1, col=1)

    # ── Bandas de Bollinger ──────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=datas, y=df["BB_upper"], name="BB+",
        line=dict(color="#7c3aed", width=1, dash="dash"), opacity=0.5,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=datas, y=df["BB_lower"], name="BB-",
        line=dict(color="#7c3aed", width=1, dash="dash"),
        fill="tonexty", fillcolor="rgba(124,58,237,0.04)", opacity=0.5,
    ), row=1, col=1)

    # ── Volume ───────────────────────────────────────────────────────────────
    cores_vol = ["#00d4aa" if c >= o else "#f43f5e" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=datas, y=df["Volume"], name="Volume", marker_color=cores_vol, opacity=0.7), row=2, col=1)
    if "Vol_media" in df.columns:
        fig.add_trace(go.Scatter(
            x=datas, y=df["Vol_media"], name="Vol Med",
            line=dict(color="#f59e0b", width=1.2, dash="dot"),
        ), row=2, col=1)

    # ── RSI ──────────────────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=datas, y=df["RSI"], name="RSI",
        line=dict(color="#a78bfa", width=1.8),
    ), row=3, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(244,63,94,0.07)",  line_width=0, row=3, col=1)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,212,170,0.07)",  line_width=0, row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#f43f5e", opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#00d4aa", opacity=0.5, row=3, col=1)
    fig.add_hline(y=50, line_dash="dot",  line_color="#64748b", opacity=0.4, row=3, col=1)

    # ── MACD ─────────────────────────────────────────────────────────────────
    cores_hist = ["#00d4aa" if v >= 0 else "#f43f5e" for v in df["Hist"]]
    fig.add_trace(go.Bar(x=datas, y=df["Hist"], name="Hist", marker_color=cores_hist, opacity=0.7), row=4, col=1)
    fig.add_trace(go.Scatter(x=datas, y=df["MACD"],   name="MACD",  line=dict(color="#0ea5e9", width=1.8)), row=4, col=1)
    fig.add_trace(go.Scatter(x=datas, y=df["Signal"], name="Sinal", line=dict(color="#f59e0b", width=1.8)), row=4, col=1)

    # ── Layout ───────────────────────────────────────────────────────────────
    fig.update_layout(
        template="plotly_dark", height=900,
        paper_bgcolor="#080c10", plot_bgcolor="#080c10",
        xaxis_rangeslider_visible=False, showlegend=True,
        legend=dict(orientation="h", x=0, y=1.08, font=dict(size=9, color="#64748b"), bgcolor="rgba(0,0,0,0)", itemwidth=40),
        margin=dict(l=60, r=20, t=80, b=20),
        font=dict(color="#e2e8f0"),
    )
    for i in range(1, 5):
        fig.update_xaxes(gridcolor="#1a2332", showgrid=True, row=i, col=1, showticklabels=(i == 4))
        fig.update_yaxes(gridcolor="#1a2332", showgrid=True, row=i, col=1)
    fig.update_xaxes(showticklabels=True, row=4, col=1)
    fig.update_yaxes(title_text="Preço", row=1, col=1, title_font=dict(size=10))
    fig.update_yaxes(title_text="Vol",   row=2, col=1, title_font=dict(size=10))
    fig.update_yaxes(title_text="RSI",   row=3, col=1, range=[0, 100], title_font=dict(size=10))
    fig.update_yaxes(title_text="MACD",  row=4, col=1, title_font=dict(size=10))
    for trace in fig.data:
        if trace.name in ["RSI", "Hist", "Sinal", "Vol Med", "Volume"]:
            trace.showlegend = False
    return fig
