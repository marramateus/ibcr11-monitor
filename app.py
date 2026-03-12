import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="IBCR11 Monitor", page_icon="📊", layout="wide")

CRIS = [
    {"nome": "CRI CRVO",       "status": "CRITICO",  "pl": 27.3, "taxa": "IPCA+7,00%",    "venc": "jun/2036",         "sec": "Virgo", "r_best": 80,  "r_base": 55,  "r_worst": 40,  "htmk": 23191.7, "uf": "RS", "tipo": "BTS",        "query": "CRVO Macromix São Leopoldo inadimplência"},
    {"nome": "CRI Olimpo",     "status": "CRITICO",  "pl": 7.2,  "taxa": "IPCA+11,00%",   "venc": "Vencido jan/2025", "sec": "True",  "r_best": 75,  "r_base": 65,  "r_worst": 50,  "htmk": 8570.6,  "uf": "SP", "tipo": "Loteamento", "query": "CRI Olimpo IBCR11 loteamento negociação"},
    {"nome": "CRI Loft",       "status": "ATENCAO",  "pl": 7.1,  "taxa": "IPCA+10,00%",   "venc": "jun/2041",         "sec": "Virgo", "r_best": 85,  "r_base": 75,  "r_worst": 60,  "htmk": 11695.4, "uf": "SP", "tipo": "Estoque",    "query": "CRI Loft Taubaté estoque residencial"},
    {"nome": "CRI Pateo II",   "status": "ATENCAO",  "pl": 10.3, "taxa": "IPCA+13,00%",   "venc": "jul/2027",         "sec": "Virgo", "r_best": 95,  "r_base": 85,  "r_worst": 75,  "htmk": 8605.4,  "uf": "SP", "tipo": "Residencial","query": "CRI Pateo Presidente Prudente entrega"},
    {"nome": "CRI Pateo III",  "status": "ATENCAO",  "pl": 7.6,  "taxa": "IPCA+12,50%",   "venc": "jul/2027",         "sec": "Virgo", "r_best": 95,  "r_base": 85,  "r_worst": 75,  "htmk": 6446.7,  "uf": "SP", "tipo": "Residencial","query": "CRI Pateo III Presidente Prudente amortização"},
    {"nome": "CRI GDP",        "status": "ATENCAO",  "pl": 3.0,  "taxa": "IPCA+10-12,5%", "venc": "out/2027",         "sec": "True",  "r_best": 90,  "r_base": 80,  "r_worst": 65,  "htmk": 2623.6,  "uf": "SC", "tipo": "Residencial","query": "Giovanni di Pietro Joinville CRI repasse"},
    {"nome": "CRI Villa Res.", "status": "NORMAL",   "pl": 8.9,  "taxa": "IPCA+9,20%",    "venc": "dez/2034",         "sec": "True",  "r_best": 100, "r_base": 95,  "r_worst": 85,  "htmk": 8874.8,  "uf": "SC", "tipo": "Residencial","query": "CRI Villa Residence Armona Itapema"},
    {"nome": "CRI Braspark",   "status": "NORMAL",   "pl": 6.1,  "taxa": "IPCA+8,00%",    "venc": "ago/2031",         "sec": "Virgo", "r_best": 100, "r_base": 95,  "r_worst": 90,  "htmk": 5407.5,  "uf": "SC", "tipo": "Logístico",  "query": "CRI Braspark Garuva galpão logístico"},
    {"nome": "CRI Vivatti",    "status": "NORMAL",   "pl": 9.0,  "taxa": "IPCA+11,00%",   "venc": "dez/2029",         "sec": "Virgo", "r_best": 100, "r_base": 95,  "r_worst": 90,  "htmk": 8503.8,  "uf": "SP", "tipo": "Residencial","query": "CRI Vivatti Presidente Prudente repasse"},
    {"nome": "CRI Maehara",    "status": "NORMAL",   "pl": 9.8,  "taxa": "IPCA+10,00%",   "venc": "dez/2031",         "sec": "Virgo", "r_best": 100, "r_base": 90,  "r_worst": 80,  "htmk": 8341.4,  "uf": "SP", "tipo": "Residencial","query": "CRI Maehara Botanik Presidente Prudente vendas"},
    {"nome": "CRI Next",       "status": "NORMAL",   "pl": 0.1,  "taxa": "IPCA+12,50%",   "venc": "out/2027",         "sec": "True",  "r_best": 100, "r_base": 100, "r_worst": 90,  "htmk": 105.2,   "uf": "ES", "tipo": "Residencial","query": "CRI Next Serra ES obras conclusão"},
]

ICON = {"CRITICO": "🔴", "ATENCAO": "🟡", "NORMAL": "🟢"}
COR  = {"CRITICO": "#E24B4A", "ATENCAO": "#EF9F27", "NORMAL": "#1D9E75"}

with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("Anthropic API Key (opcional)", type="password")
    st.divider()
    filtro = st.multiselect("Filtrar por status", ["CRITICO", "ATENCAO", "NORMAL"],
                            default=["CRITICO", "ATENCAO", "NORMAL"])
    st.divider()
    st.caption("Base: Jan/2026 | Gestor: BREI")

st.title("IBCR11 — Monitor de CRIs")
c1, c2, c3, c4 = st.columns(4)
c1.metric("VP (cota patrimonial)", "R$ 90,33", "-R$ 0,72")
c2.metric("VM (cota mercado)",     "R$ 49,24", "+R$ 0,59")
c3.metric("Desagio VM/VP",         "45,49%",   "+1,08 pp", delta_color="inverse")
c4.metric("DY Mensal jan/26",      "1,22%",    "-0,22 pp", delta_color="inverse")
st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["Carteira", "Monitorar CRIs", "Cotacao", "Stress Test"])

# TAB 1
with tab1:
    cris_f = [c for c in CRIS if c["status"] in filtro]
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Composicao por status")
        df_pie = pd.DataFrame([
            {"Status": s, "PL": sum(c["pl"] for c in CRIS if c["status"] == s)}
            for s in ["CRITICO", "ATENCAO", "NORMAL"]
        ])
        fig1 = px.pie(df_pie, names="Status", values="PL",
                      color="Status", color_discrete_map=COR, hole=0.3)
        fig1.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        st.subheader("Composicao por tipo")
        df_tipo = pd.DataFrame([{"Tipo": c["tipo"], "PL": c["pl"]} for c in CRIS])
        df_tipo = df_tipo.groupby("Tipo", as_index=False).sum().sort_values("PL")
        fig2 = px.bar(df_tipo, x="PL", y="Tipo", orientation="h",
                      color_discrete_sequence=["#378ADD"])
        fig2.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Recovery por cenario (%)")
    nomes = [c["nome"] for c in cris_f]
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Best",  x=nomes, y=[c["r_best"]  for c in cris_f], marker_color="#1D9E75", opacity=0.6))
    fig3.add_trace(go.Bar(name="Base",  x=nomes, y=[c["r_base"]  for c in cris_f], marker_color="#378ADD"))
    fig3.add_trace(go.Bar(name="Worst", x=nomes, y=[c["r_worst"] for c in cris_f], marker_color="#E24B4A", opacity=0.7))
    fig3.update_layout(barmode="group", height=320, yaxis_title="%",
                       margin=dict(t=10,b=10,l=10,r=10), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Tabela")
    df_t = pd.DataFrame([{
        "": ICON[c["status"]], "Ativo": c["nome"], "Status": c["status"],
        "% PL": c["pl"], "Taxa": c["taxa"], "Venc": c["venc"],
        "Sec": c["sec"], "HTM Rk": c["htmk"], "Recovery Base": c["r_base"],
    } for c in cris_f])
    st.dataframe(df_t, use_container_width=True, hide_index=True)

# TAB 2
with tab2:
    st.subheader("Busca de noticias por CRI")
    cri_sel = st.selectbox("CRI", [c["nome"] for c in CRIS],
                           format_func=lambda x: f"{ICON[next(c['status'] for c in CRIS if c['nome']==x)]} {x}")
    cri = next(c for c in CRIS if c["nome"] == cri_sel)
    query = st.text_input("Query (editavel)", value=cri["query"])

    b1, b2, _ = st.columns([1,1,5])
    btn1 = b1.button("Buscar este", type="primary")
    btn2 = b2.button("Buscar todos")

    def buscar_google_rss(q):
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
        soup = BeautifulSoup(r.content, "xml")
        items = soup.find_all("item")
        if not items:
            return []
        return [{"titulo": i.find("title").text, "link": i.find("link").text,
                 "data": i.find("pubDate").text[:16] if i.find("pubDate") else ""}
                for i in items[:6]]

    def buscar_bing_rss(q):
        url = f"https://www.bing.com/news/search?q={requests.utils.quote(q)}&format=rss"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10)
        soup = BeautifulSoup(r.content, "xml")
        items = soup.find_all("item")
        if not items:
            return []
        return [{"titulo": i.find("title").text, "link": i.find("link").text,
                 "data": i.find("pubDate").text[:16] if i.find("pubDate") else ""}
                for i in items[:6]]

    def buscar(q):
        erros = []
        for fonte, fn in [("Google News", buscar_google_rss), ("Bing News", buscar_bing_rss)]:
            try:
                resultados = fn(q)
                if resultados:
                    st.caption(f"Fonte: {fonte}")
                    return resultados
            except Exception as e:
                erros.append(f"{fonte}: {e}")
        if erros:
            st.error("Falha em todas as fontes:\n" + "\n".join(erros))
        return []

    def sintetizar(key, nome, noticias):
        if not key or not noticias:
            return None
        try:
            textos = "\n".join(f"- {n['titulo']}" for n in noticias)
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 200,
                      "messages": [{"role": "user", "content":
                          f"Sintetize em 2-3 frases as novidades sobre {nome} (CRI do IBCR11). "
                          f"Diga se o status melhorou, piorou ou estavel.\n\n{textos}"}]},
                timeout=20
            )
            return r.json()["content"][0]["text"]
        except Exception as e:
            return f"Erro IA: {e}"

    def mostrar(alvo, q):
        st.markdown(f"#### {ICON[alvo['status']]} {alvo['nome']} — {alvo['status']}")
        st.caption(f"{alvo['taxa']} | Venc: {alvo['venc']} | {alvo['pl']}% do PL")
        with st.spinner("Buscando..."):
            noticias = buscar(q)
        if not noticias:
            st.warning("Nenhuma noticia encontrada. Tente uma query mais simples.")
        else:
            if api_key:
                with st.spinner("Sintetizando..."):
                    s = sintetizar(api_key, alvo["nome"], noticias)
                if s:
                    st.info(s)
            for n in noticias:
                st.markdown(f"- [{n['titulo']}]({n['link']}) `{n['data']}`")

    if btn1:
        mostrar(cri, query)
    elif btn2:
        for alvo in CRIS:
            mostrar(alvo, alvo["query"])
            st.divider()
    else:
        st.info(f"{ICON[cri['status']]} **{cri['nome']}** — {cri['taxa']} | {cri['venc']} | {cri['pl']}% do PL")

# TAB 3
with tab3:
    st.subheader("Cotacao IBCR11 — ultimos 3 meses")

    @st.cache_data(ttl=900)
    def get_cotacao():
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/IBCR11.SA?interval=1d&range=3mo"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            d = r.json()["chart"]["result"][0]
            df = pd.DataFrame({
                "data":       [datetime.fromtimestamp(t).strftime("%Y-%m-%d") for t in d["timestamp"]],
                "fechamento": d["indicators"]["quote"][0]["close"],
                "volume":     d["indicators"]["quote"][0]["volume"],
            }).dropna()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar cotacao: {e}")
            return None

    df_cot = get_cotacao()
    if df_cot is not None:
        u = df_cot.iloc[-1]
        m1, m2, m3 = st.columns(3)
        m1.metric("Ultimo fechamento",   f"R$ {u['fechamento']:.2f}")
        m2.metric("Volume ultimo pregao", f"{int(u['volume']):,}" if pd.notna(u["volume"]) else "—")
        m3.metric("Desagio sobre VP",     f"{(1 - u['fechamento']/90.33)*100:.1f}%", delta_color="inverse")

        fc = go.Figure()
        fc.add_trace(go.Scatter(x=df_cot["data"], y=df_cot["fechamento"],
                                mode="lines", name="Fechamento",
                                line=dict(color="#378ADD", width=2)))
        fc.add_hline(y=90.33, line_dash="dash", line_color="#E24B4A", annotation_text="VP R$90,33")
        fc.update_layout(height=350, yaxis_title="R$", margin=dict(t=20,b=20,l=10,r=80))
        st.plotly_chart(fc, use_container_width=True)

        fv = px.bar(df_cot, x="data", y="volume", title="Volume diario (cotas)",
                    color_discrete_sequence=["#9FE1CB"])
        fv.update_layout(height=200, margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fv, use_container_width=True)

    st.subheader("Tabela de sensibilidade")
    sens = pd.DataFrame([
        (41.74,-53.79,21.01,18.68,22.02),(43.24,-52.13,20.28,17.98,21.25),
        (44.74,-50.47,19.60,17.33,20.54),(46.24,-48.81,18.96,16.73,19.87),
        (47.74,-47.15,18.37,16.17,19.25),(49.24,-45.49,17.81,15.64,18.66),
        (50.74,-43.83,17.28,15.15,18.11),(52.24,-42.17,16.79,14.69,17.59),
        (53.74,-40.51,16.32,14.25,17.10),(55.24,-38.84,15.87,13.84,16.64),
    ], columns=["Cota (R$)","Desagio (%)","Taxa IPCA+","DY 1M (%)","DY 12M (%)"])
    st.dataframe(sens, use_container_width=True, hide_index=True)

# TAB 4
with tab4:
    st.subheader("Stress Test — best / base / worst")
    COTAS = 958423
    df_st = pd.DataFrame([{
        "Ativo": c["nome"], "% PL": c["pl"],
        "Best %": c["r_best"], "Base %": c["r_base"], "Worst %": c["r_worst"],
        "HTM Rk": c["htmk"],
        "Best Rk":  round(c["htmk"] * c["r_best"]  / 100),
        "Base Rk":  round(c["htmk"] * c["r_base"]  / 100),
        "Worst Rk": round(c["htmk"] * c["r_worst"] / 100),
    } for c in CRIS])

    best_mi  = df_st["Best Rk"].sum()  / 1000
    base_mi  = df_st["Base Rk"].sum()  / 1000
    worst_mi = df_st["Worst Rk"].sum() / 1000

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("PL Contabil",  "R$ 86.6 mi",          "R$ 90,33/cota")
    k2.metric("PL Best",      f"R$ {best_mi:.1f} mi", f"R$ {best_mi*1e6/COTAS:.2f}/cota")
    k3.metric("PL Base",      f"R$ {base_mi:.1f} mi", f"R$ {base_mi*1e6/COTAS:.2f}/cota")
    k4.metric("PL Worst",     f"R$ {worst_mi:.1f} mi",f"R$ {worst_mi*1e6/COTAS:.2f}/cota", delta_color="inverse")

    fs = go.Figure()
    nomes = df_st["Ativo"].tolist()
    fs.add_trace(go.Bar(name="Best",  x=nomes, y=df_st["Best Rk"],  marker_color="#1D9E75", opacity=0.6))
    fs.add_trace(go.Bar(name="Base",  x=nomes, y=df_st["Base Rk"],  marker_color="#378ADD"))
    fs.add_trace(go.Bar(name="Worst", x=nomes, y=df_st["Worst Rk"], marker_color="#E24B4A", opacity=0.7))
    fs.update_layout(barmode="group", height=380, yaxis_title="R$ mil",
                     margin=dict(t=10,b=10,l=10,r=10), legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fs, use_container_width=True)

    st.dataframe(df_st, use_container_width=True, hide_index=True)

    st.subheader("IRR esperado — comprado a ~R$ 49/cota")
    irr = pd.DataFrame([
        ("Positivo", "CRVO + Olimpo resolvidos",        "~20%",       "~R$73/cota", "+49%", "34-38%"),
        ("Base",     "Mercado aceita VP ajustado",       "~25-30%",    "~R$61/cota", "+25%", "23-26%"),
        ("Ruim",     "CRVO 45%, Olimpo piora",           "~40%",       "~R$52/cota", "+6%",  "14-16%"),
        ("Stress",   "Worst case, desagio se mantem 30%","~30% s/ VP", "~R$40/cota", "-18%", "~0-3%"),
    ], columns=["Cenario","Hipotese","Desagio Final","VM em 24M","Ganho Capital","IRR a.a."])
    st.dataframe(irr, use_container_width=True, hide_index=True)

    st.info(
        "Perda estimada cenario base: ~26% do PL. "
        "Desagio atual 45,5% — ~26pp justificado por risco real, ~19pp por incerteza/liquidez. "
        "Mesmo no worst case o fundo nao quebra. "
        "Perfil: credito especial/distressed — nao e fundo conservador."
    )