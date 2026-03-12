import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from io import StringIO
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import plotly.express as px
 
st.set_page_config(page_title="IBCR11 Monitor", page_icon="📊", layout="wide")
 
CNPJ_IBCR11 = "14744231000114"
 
CRIS = [
    {"nome": "CRI CRVO",       "status": "CRITICO",  "pl": 27.3, "taxa": "IPCA+7,00%",    "venc": "jun/2036",         "sec": "Virgo", "r_best": 80,  "r_base": 55,  "r_worst": 40,  "htmk": 23191.7, "uf": "RS", "tipo": "BTS",        "query": "CRVO Macromix Sao Leopoldo inadimplencia"},
    {"nome": "CRI Olimpo",     "status": "CRITICO",  "pl": 7.2,  "taxa": "IPCA+11,00%",   "venc": "Vencido jan/2025", "sec": "True",  "r_best": 75,  "r_base": 65,  "r_worst": 50,  "htmk": 8570.6,  "uf": "SP", "tipo": "Loteamento", "query": "CRI Olimpo IBCR11 loteamento negociacao"},
    {"nome": "CRI Loft",       "status": "ATENCAO",  "pl": 7.1,  "taxa": "IPCA+10,00%",   "venc": "jun/2041",         "sec": "Virgo", "r_best": 85,  "r_base": 75,  "r_worst": 60,  "htmk": 11695.4, "uf": "SP", "tipo": "Estoque",    "query": "CRI Loft Taubate estoque residencial"},
    {"nome": "CRI Pateo II",   "status": "ATENCAO",  "pl": 10.3, "taxa": "IPCA+13,00%",   "venc": "jul/2027",         "sec": "Virgo", "r_best": 95,  "r_base": 85,  "r_worst": 75,  "htmk": 8605.4,  "uf": "SP", "tipo": "Residencial","query": "CRI Pateo Presidente Prudente entrega"},
    {"nome": "CRI Pateo III",  "status": "ATENCAO",  "pl": 7.6,  "taxa": "IPCA+12,50%",   "venc": "jul/2027",         "sec": "Virgo", "r_best": 95,  "r_base": 85,  "r_worst": 75,  "htmk": 6446.7,  "uf": "SP", "tipo": "Residencial","query": "CRI Pateo III Presidente Prudente amortizacao"},
    {"nome": "CRI GDP",        "status": "ATENCAO",  "pl": 3.0,  "taxa": "IPCA+10-12,5%", "venc": "out/2027",         "sec": "True",  "r_best": 90,  "r_base": 80,  "r_worst": 65,  "htmk": 2623.6,  "uf": "SC", "tipo": "Residencial","query": "Giovanni di Pietro Joinville CRI repasse"},
    {"nome": "CRI Villa Res.", "status": "NORMAL",   "pl": 8.9,  "taxa": "IPCA+9,20%",    "venc": "dez/2034",         "sec": "True",  "r_best": 100, "r_base": 95,  "r_worst": 85,  "htmk": 8874.8,  "uf": "SC", "tipo": "Residencial","query": "CRI Villa Residence Armona Itapema"},
    {"nome": "CRI Braspark",   "status": "NORMAL",   "pl": 6.1,  "taxa": "IPCA+8,00%",    "venc": "ago/2031",         "sec": "Virgo", "r_best": 100, "r_base": 95,  "r_worst": 90,  "htmk": 5407.5,  "uf": "SC", "tipo": "Logistico",  "query": "CRI Braspark Garuva galpao logistico"},
    {"nome": "CRI Vivatti",    "status": "NORMAL",   "pl": 9.0,  "taxa": "IPCA+11,00%",   "venc": "dez/2029",         "sec": "Virgo", "r_best": 100, "r_base": 95,  "r_worst": 90,  "htmk": 8503.8,  "uf": "SP", "tipo": "Residencial","query": "CRI Vivatti Presidente Prudente repasse"},
    {"nome": "CRI Maehara",    "status": "NORMAL",   "pl": 9.8,  "taxa": "IPCA+10,00%",   "venc": "dez/2031",         "sec": "Virgo", "r_best": 100, "r_base": 90,  "r_worst": 80,  "htmk": 8341.4,  "uf": "SP", "tipo": "Residencial","query": "CRI Maehara Botanik Presidente Prudente vendas"},
    {"nome": "CRI Next",       "status": "NORMAL",   "pl": 0.1,  "taxa": "IPCA+12,50%",   "venc": "out/2027",         "sec": "True",  "r_best": 100, "r_base": 100, "r_worst": 90,  "htmk": 105.2,   "uf": "ES", "tipo": "Residencial","query": "CRI Next Serra ES obras conclusao"},
]
 
ICON = {"CRITICO": "🔴", "ATENCAO": "🟡", "NORMAL": "🟢"}
COR  = {"CRITICO": "#E24B4A", "ATENCAO": "#EF9F27", "NORMAL": "#1D9E75"}
 
FALLBACK_CVM = {
    "vp": 90.33, "vp_delta": -0.72,
    "dy_mensal": 1.22, "dy_delta": -0.22,
    "pl_total": 86572000.0,
    "cotas": 958423,
    "dividendo_cota": 0.60,
    "competencia": "2026-01",
    "fonte": "estatico (jan/2026)"
}
 
# ── Gera lista de meses disponíveis (jun/2021 até hoje) ──────────────────────
def gerar_meses():
    inicio = date(2021, 6, 1)
    hoje = date.today()
    meses = []
    d = date(inicio.year, inicio.month, 1)
    while d <= date(hoje.year, hoje.month, 1):
        meses.append(d.strftime("%Y-%m"))
        if d.month == 12:
            d = date(d.year + 1, 1, 1)
        else:
            d = date(d.year, d.month + 1, 1)
    return list(reversed(meses))  # mais recente primeiro
 
MESES = gerar_meses()
LABELS = {m: datetime.strptime(m, "%Y-%m").strftime("%b/%Y").lower() for m in MESES}
 
# ── CVM: carrega CSV anual completo ──────────────────────────────────────────
@st.cache_data(ttl=3600)
def carregar_csv_cvm(ano):
    url = f"https://dados.cvm.gov.br/dados/FII/doc/inf_mensal/dados/inf_mensal_fii_{ano}.csv"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or len(r.content) < 500:
            return None
        df = pd.read_csv(StringIO(r.text), sep=";", encoding="latin1", dtype=str)
        df.columns = df.columns.str.strip().str.upper()
        cnpj_col = next((c for c in df.columns if "CNPJ" in c and "FUNDO" in c), None)
        if cnpj_col is None:
            return None
        df = df[df[cnpj_col].str.replace(r"\D", "", regex=True) == CNPJ_IBCR11].copy()
        return df if not df.empty else None
    except:
        return None
 
def get_dados_cvm_mes(ano_mes):
    ano = int(ano_mes[:4])
    dfs = []
    for a in [ano, ano - 1]:
        df = carregar_csv_cvm(a)
        if df is not None:
            dfs.append(df)
    if not dfs:
        return {**FALLBACK_CVM, "fonte": "CVM indisponivel — usando estatico"}
 
    df_all = pd.concat(dfs, ignore_index=True)
    data_col = next((c for c in df_all.columns if any(x in c for x in ["COMPET", "DT_REF", "DATA"])), None)
    if data_col is None:
        return {**FALLBACK_CVM, "fonte": "coluna data nao encontrada"}
 
    # Normaliza para YYYY-MM
    df_all["_mes"] = pd.to_datetime(df_all[data_col], errors="coerce").dt.strftime("%Y-%m")
    df_mes = df_all[df_all["_mes"] == ano_mes]
 
    if df_mes.empty:
        return {**FALLBACK_CVM, "fonte": f"sem dado CVM para {LABELS.get(ano_mes, ano_mes)}"}
 
    row = df_mes.iloc[-1]
 
    def v(chave, default=None):
        col = next((c for c in df_mes.columns if chave in c), None)
        if col is None:
            return default
        try:
            return float(str(row[col]).replace(",", "."))
        except:
            return default
 
    vp        = v("VL_PATRIM_COTA",    FALLBACK_CVM["vp"])
    pl        = v("VL_PATRIM_LIQ",     FALLBACK_CVM["pl_total"])
    cotas     = v("NR_COTAS",          FALLBACK_CVM["cotas"])
    dividendo = v("VL_RENDIMENTO",     FALLBACK_CVM["dividendo_cota"])
    dy        = round(dividendo / vp * 100, 2) if vp and dividendo else FALLBACK_CVM["dy_mensal"]
    label     = LABELS.get(ano_mes, ano_mes)
 
    return {
        "vp": vp or FALLBACK_CVM["vp"],
        "vp_delta": 0.0,
        "dy_mensal": dy,
        "dy_delta": 0.0,
        "pl_total": pl or FALLBACK_CVM["pl_total"],
        "cotas": int(cotas) if cotas else FALLBACK_CVM["cotas"],
        "dividendo_cota": dividendo or FALLBACK_CVM["dividendo_cota"],
        "competencia": ano_mes,
        "fonte": f"CVM ({label})"
    }
 
# ── Cotação histórica (Yahoo Finance) ────────────────────────────────────────
@st.cache_data(ttl=900)
def get_cotacao(periodo):
    # periodo: "1mo","3mo","6mo","1y","2y","5y"
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/IBCR11.SA?interval=1d&range={periodo}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        d = r.json()["chart"]["result"][0]
        df = pd.DataFrame({
            "data":       [datetime.fromtimestamp(t).strftime("%Y-%m-%d") for t in d["timestamp"]],
            "fechamento": d["indicators"]["quote"][0]["close"],
            "volume":     d["indicators"]["quote"][0]["volume"],
        }).dropna()
        return df
    except:
        return None
 
# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Periodo de referencia")
 
    mes_sel = st.selectbox(
        "Mes/Ano",
        MESES,
        format_func=lambda m: LABELS[m],
        index=0
    )
 
    periodo_cotacao = st.select_slider(
        "Historico B3",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        value="3mo"
    )
 
    st.divider()
    api_key = st.text_input("Anthropic API Key (opcional)", type="password")
    filtro = st.multiselect("Filtrar CRIs por status",
                            ["CRITICO", "ATENCAO", "NORMAL"],
                            default=["CRITICO", "ATENCAO", "NORMAL"])
    st.divider()
    if st.button("Limpar cache"):
        st.cache_data.clear()
        st.rerun()
 
# ── Carrega dados do mês selecionado ─────────────────────────────────────────
cvm     = get_dados_cvm_mes(mes_sel)
cotacao = get_cotacao(periodo_cotacao)
 
vm      = cotacao.iloc[-1]["fechamento"] if cotacao is not None else 49.24
desagio = round((1 - vm / cvm["vp"]) * 100, 2)
 
# ── Header KPIs ───────────────────────────────────────────────────────────────
st.title("IBCR11 — Monitor de CRIs")
st.caption(f"Dados fundamentais: {cvm['fonte']} | Cotacao: Yahoo Finance (15min delay)")
 
c1, c2, c3, c4 = st.columns(4)
c1.metric("VP (cota patrimonial)", f"R$ {cvm['vp']:.2f}")
c2.metric("VM (cota mercado)",     f"R$ {vm:.2f}")
c3.metric("Desagio VM/VP",         f"{desagio:.2f}%", delta_color="inverse")
c4.metric("DY Mensal",             f"{cvm['dy_mensal']:.2f}%")
st.divider()
 
tab1, tab2, tab3, tab4 = st.tabs(["Carteira", "Monitorar CRIs", "Cotacao", "Stress Test"])
 
# ── TAB 1 ─────────────────────────────────────────────────────────────────────
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
 
# ── TAB 2 ─────────────────────────────────────────────────────────────────────
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
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        items = soup.find_all("item")
        if not items:
            return []
        return [{"titulo": i.find("title").text if i.find("title") else "",
                 "link": i.find("link").text if i.find("link") else "",
                 "data": i.find("pubdate").text[:16] if i.find("pubdate") else ""}
                for i in items[:6]]
 
    def buscar_bing_rss(q):
        url = f"https://www.bing.com/news/search?q={requests.utils.quote(q)}&format=rss"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        items = soup.find_all("item")
        if not items:
            return []
        return [{"titulo": i.find("title").text if i.find("title") else "",
                 "link": i.find("link").text if i.find("link") else "",
                 "data": i.find("pubdate").text[:16] if i.find("pubdate") else ""}
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
 
# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    label_periodo = {"1mo":"1 mes","3mo":"3 meses","6mo":"6 meses","1y":"1 ano","2y":"2 anos","5y":"5 anos"}
    st.subheader(f"Cotacao IBCR11 — {label_periodo.get(periodo_cotacao, periodo_cotacao)}")
 
    if cotacao is not None:
        u = cotacao.iloc[-1]
        m1, m2, m3 = st.columns(3)
        m1.metric("Ultimo fechamento",    f"R$ {u['fechamento']:.2f}")
        m2.metric("Volume ultimo pregao", f"{int(u['volume']):,}" if pd.notna(u["volume"]) else "—")
        m3.metric("Desagio sobre VP",     f"{(1 - u['fechamento']/cvm['vp'])*100:.1f}%", delta_color="inverse")
 
        # Linha VP do mês selecionado
        fc = go.Figure()
        fc.add_trace(go.Scatter(x=cotacao["data"], y=cotacao["fechamento"],
                                mode="lines", name="Fechamento",
                                line=dict(color="#378ADD", width=2)))
        fc.add_hline(y=cvm["vp"], line_dash="dash", line_color="#E24B4A",
                     annotation_text=f"VP {LABELS[mes_sel]} R${cvm['vp']:.2f}")
        fc.update_layout(height=380, yaxis_title="R$", margin=dict(t=20,b=20,l=10,r=120))
        st.plotly_chart(fc, use_container_width=True)
 
        fv = px.bar(cotacao, x="data", y="volume", title="Volume diario (cotas)",
                    color_discrete_sequence=["#9FE1CB"])
        fv.update_layout(height=200, margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fv, use_container_width=True)
    else:
        st.error("Nao foi possivel carregar a cotacao.")
 
    st.subheader("Tabela de sensibilidade")
    sens = pd.DataFrame([
        (41.74,-53.79,21.01,18.68,22.02),(43.24,-52.13,20.28,17.98,21.25),
        (44.74,-50.47,19.60,17.33,20.54),(46.24,-48.81,18.96,16.73,19.87),
        (47.74,-47.15,18.37,16.17,19.25),(49.24,-45.49,17.81,15.64,18.66),
        (50.74,-43.83,17.28,15.15,18.11),(52.24,-42.17,16.79,14.69,17.59),
        (53.74,-40.51,16.32,14.25,17.10),(55.24,-38.84,15.87,13.84,16.64),
    ], columns=["Cota (R$)","Desagio (%)","Taxa IPCA+","DY 1M (%)","DY 12M (%)"])
    st.dataframe(sens, use_container_width=True, hide_index=True)
 
# ── TAB 4 ─────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Stress Test — best / base / worst")
 
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
    pl_mi    = cvm["pl_total"] / 1e6
    cotas_n  = cvm["cotas"]
 
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("PL Contabil",  f"R$ {pl_mi:.1f} mi",     f"R$ {cvm['vp']:.2f}/cota")
    k2.metric("PL Best",      f"R$ {best_mi:.1f} mi",   f"R$ {best_mi*1e6/cotas_n:.2f}/cota")
    k3.metric("PL Base",      f"R$ {base_mi:.1f} mi",   f"R$ {base_mi*1e6/cotas_n:.2f}/cota")
    k4.metric("PL Worst",     f"R$ {worst_mi:.1f} mi",  f"R$ {worst_mi*1e6/cotas_n:.2f}/cota", delta_color="inverse")
 
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
        ("Positivo", "CRVO + Olimpo resolvidos",         "~20%",       "~R$73/cota", "+49%", "34-38%"),
        ("Base",     "Mercado aceita VP ajustado",        "~25-30%",    "~R$61/cota", "+25%", "23-26%"),
        ("Ruim",     "CRVO 45%, Olimpo piora",            "~40%",       "~R$52/cota", "+6%",  "14-16%"),
        ("Stress",   "Worst case, desagio se mantem 30%", "~30% s/ VP", "~R$40/cota", "-18%", "~0-3%"),
    ], columns=["Cenario","Hipotese","Desagio Final","VM em 24M","Ganho Capital","IRR a.a."])
    st.dataframe(irr, use_container_width=True, hide_index=True)
 
    st.info(
        "Perda estimada cenario base: ~26% do PL. "
        "Desagio atual 45,5% — ~26pp justificado por risco real, ~19pp por incerteza/liquidez. "
        "Mesmo no worst case o fundo nao quebra. "
        "Perfil: credito especial/distressed — nao e fundo conservador."
    )
 
