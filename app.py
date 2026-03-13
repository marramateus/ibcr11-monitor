import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from io import StringIO
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="IBCR11 Monitor", page_icon="📊", layout="wide")

# ── Constantes ────────────────────────────────────────────────────────────────
CNPJ_IBCR11 = "14744231000114"
TICKER      = "IBCR11.SA"

# Dados de carteira (só mudam com relatório do gestor — fonte: BREI jan/2026)
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

# ── Helpers ───────────────────────────────────────────────────────────────────
def gerar_meses():
    inicio = date(2021, 6, 1)
    hoje   = date.today()
    meses  = []
    d = date(inicio.year, inicio.month, 1)
    while d <= date(hoje.year, hoje.month, 1):
        meses.append(d.strftime("%Y-%m"))
        d = date(d.year + (d.month // 12), (d.month % 12) + 1, 1)
    return list(reversed(meses))

MESES  = gerar_meses()
LABELS = {m: datetime.strptime(m, "%Y-%m").strftime("%b/%Y").lower() for m in MESES}

# ── CVM: carrega CSV anual ────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_csv_cvm(ano: int):
    url = f"https://dados.cvm.gov.br/dados/FII/doc/inf_mensal/dados/inf_mensal_fii_{ano}.csv"
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text), sep=";", encoding="latin1", dtype=str)
    df.columns = df.columns.str.strip().str.upper()
    cnpj_col = next((c for c in df.columns if "CNPJ" in c and "FUNDO" in c), None)
    if not cnpj_col:
        raise ValueError(f"Coluna CNPJ nao encontrada no CSV {ano}. Colunas: {list(df.columns)}")
    df = df[df[cnpj_col].str.replace(r"\D", "", regex=True) == CNPJ_IBCR11].copy()
    if df.empty:
        raise ValueError(f"IBCR11 nao encontrado no CSV {ano}")
    return df

def get_dados_cvm_mes(ano_mes: str):
    """Retorna dict com dados do mes ou lanca excecao com mensagem clara."""
    ano = int(ano_mes[:4])
    erros = []
    df_all = None

    for a in ([ano, ano - 1] if ano == date.today().year else [ano]):
        try:
            df = carregar_csv_cvm(a)
            df_all = df if df_all is None else pd.concat([df_all, df], ignore_index=True)
        except Exception as e:
            erros.append(f"CSV {a}: {e}")

    if df_all is None or df_all.empty:
        raise ConnectionError("CVM indisponivel:\n" + "\n".join(erros))

    data_col = next((c for c in df_all.columns if any(x in c for x in ["COMPET", "DT_REF", "DATA"])), None)
    if not data_col:
        raise ValueError(f"Coluna de data nao encontrada. Colunas: {list(df_all.columns)}")

    df_all["_mes"] = pd.to_datetime(df_all[data_col], errors="coerce").dt.strftime("%Y-%m")
    df_mes = df_all[df_all["_mes"] == ano_mes]

    if df_mes.empty:
        meses_disp = sorted(df_all["_mes"].dropna().unique().tolist())
        raise ValueError(f"Sem dado CVM para {LABELS.get(ano_mes, ano_mes)}.\nMeses disponiveis: {meses_disp}")

    row = df_mes.iloc[-1]

    def v(chave):
        col = next((c for c in df_mes.columns if chave in c), None)
        if col is None:
            raise KeyError(f"Campo '{chave}' nao encontrado. Colunas disponiveis: {[c for c in df_mes.columns if any(x in c for x in ['VL','NR','QT'])]}")
        raw = str(row[col]).replace(",", ".")
        if raw in ("", "nan", "None"):
            raise ValueError(f"Campo '{col}' vazio para {ano_mes}")
        return float(raw)

    vp        = v("VL_PATRIM_COTA")
    pl        = v("VL_PATRIM_LIQ")
    cotas     = v("NR_COTAS")
    dividendo = v("VL_RENDIMENTO")
    cotistas  = v("NR_COTST") if any("COTST" in c for c in df_mes.columns) else None
    dy        = round(dividendo / vp * 100, 4) if vp else None

    return {
        "vp": vp, "pl_total": pl, "cotas": int(cotas),
        "dividendo_cota": dividendo, "dy_mensal": dy,
        "cotistas": int(cotistas) if cotistas else None,
        "competencia": ano_mes,
        "label": LABELS.get(ano_mes, ano_mes),
    }

# ── Yahoo Finance ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def get_cotacao(periodo: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}?interval=1d&range={periodo}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    result = r.json()["chart"]["result"]
    if not result:
        raise ValueError(f"Yahoo Finance nao retornou dados para {TICKER}")
    d  = result[0]
    df = pd.DataFrame({
        "data":       [datetime.fromtimestamp(t).strftime("%Y-%m-%d") for t in d["timestamp"]],
        "fechamento": d["indicators"]["quote"][0]["close"],
        "volume":     d["indicators"]["quote"][0]["volume"],
    }).dropna(subset=["fechamento"])
    if df.empty:
        raise ValueError("Serie de cotacoes vazia")
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Periodo")
    mes_sel = st.selectbox("Mes/Ano (CVM)", MESES, format_func=lambda m: LABELS[m], index=0)
    periodo_graf = st.select_slider(
        "Historico B3",
        options=["1mo","3mo","6mo","1y","2y","5y"],
        value="3mo"
    )
    st.divider()
    api_key = st.text_input("Anthropic API Key (opcional)", type="password")
    filtro  = st.multiselect("Filtrar CRIs", ["CRITICO","ATENCAO","NORMAL"],
                             default=["CRITICO","ATENCAO","NORMAL"])
    st.divider()
    if st.button("Limpar cache"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Fonte: CVM (informe mensal FII) + Yahoo Finance")

# ── Carrega dados ─────────────────────────────────────────────────────────────
st.title("IBCR11 — Monitor de CRIs")

# CVM
cvm_ok, cvm, cvm_erro = False, None, None
try:
    with st.spinner(f"Carregando CVM ({LABELS[mes_sel]})..."):
        cvm = get_dados_cvm_mes(mes_sel)
    cvm_ok = True
except Exception as e:
    cvm_erro = str(e)

# Cotacao
cot_ok, cotacao, cot_erro = False, None, None
try:
    with st.spinner("Carregando cotacao (Yahoo Finance)..."):
        cotacao = get_cotacao(periodo_graf)
    cot_ok = True
except Exception as e:
    cot_erro = str(e)

# ── Header KPIs ───────────────────────────────────────────────────────────────
if cvm_ok and cot_ok:
    vm      = cotacao.iloc[-1]["fechamento"]
    desagio = round((1 - vm / cvm["vp"]) * 100, 2)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("VP/cota",        f"R$ {cvm['vp']:.2f}",       help=f"CVM — {cvm['label']}")
    c2.metric("VM/cota (B3)",   f"R$ {vm:.2f}",              help="Yahoo Finance — 15min delay")
    c3.metric("Desagio VM/VP",  f"{desagio:.2f}%",            delta_color="inverse")
    c4.metric("DY Mensal",      f"{cvm['dy_mensal']:.2f}%",  help=f"Dividendo R${cvm['dividendo_cota']:.2f}/cota")
    st.caption(f"CVM: {cvm['label']} | PL: R$ {cvm['pl_total']/1e6:.1f} mi | {cvm['cotas']:,} cotas" +
               (f" | {cvm['cotistas']:,} cotistas" if cvm.get('cotistas') else ""))
elif cvm_ok and not cot_ok:
    c1,c2,c3 = st.columns(3)
    c1.metric("VP/cota",       f"R$ {cvm['vp']:.2f}",      help=f"CVM — {cvm['label']}")
    c2.metric("DY Mensal",     f"{cvm['dy_mensal']:.2f}%")
    c3.metric("PL",            f"R$ {cvm['pl_total']/1e6:.1f} mi")
    st.error(f"Cotacao B3 indisponivel: {cot_erro}")
elif cot_ok and not cvm_ok:
    vm = cotacao.iloc[-1]["fechamento"]
    c1,c2 = st.columns(2)
    c1.metric("VM/cota (B3)",  f"R$ {vm:.2f}")
    c2.metric("VP/cota",       "— erro CVM")
    st.error(f"CVM indisponivel:\n```\n{cvm_erro}\n```")
else:
    st.error(f"Todas as fontes falharam.\n\nCVM: {cvm_erro}\n\nYahoo: {cot_erro}")
    st.stop()

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Carteira", "Monitorar CRIs", "Cotacao", "Stress Test"])

# ── TAB 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    cris_f = [c for c in CRIS if c["status"] in filtro]

    if not cris_f:
        st.warning("Nenhum CRI selecionado — ajuste o filtro na sidebar.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Composicao por status")
            df_pie = pd.DataFrame([
                {"Status": s, "PL": sum(c["pl"] for c in CRIS if c["status"] == s)}
                for s in ["CRITICO","ATENCAO","NORMAL"]
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
        fig3  = go.Figure()
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

    st.caption("Composicao da carteira: BREI — Relatorio jan/2026. Atualizar manualmente apos novo relatorio.")

# ── TAB 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Busca de noticias por CRI")
    cri_sel = st.selectbox("CRI", [c["nome"] for c in CRIS],
                           format_func=lambda x: f"{ICON[next(c['status'] for c in CRIS if c['nome']==x)]} {x}")
    cri_obj = next(c for c in CRIS if c["nome"] == cri_sel)
    query   = st.text_input("Query (editavel)", value=cri_obj["query"])

    b1, b2, _ = st.columns([1,1,5])
    btn1 = b1.button("Buscar este", type="primary")
    btn2 = b2.button("Buscar todos")

    def buscar_rss(q, url):
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10)
        r.raise_for_status()
        soup  = BeautifulSoup(r.content, "html.parser")
        items = soup.find_all("item")
        return [{"titulo": i.find("title").text if i.find("title") else "",
                 "link":   i.find("link").text if i.find("link") else "",
                 "data":   i.find("pubdate").text[:16] if i.find("pubdate") else ""}
                for i in items[:6]]

    def buscar(q):
        fontes = [
            ("Google News", f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"),
            ("Bing News",   f"https://www.bing.com/news/search?q={requests.utils.quote(q)}&format=rss"),
        ]
        erros = []
        for nome_fonte, url in fontes:
            try:
                res = buscar_rss(q, url)
                if res:
                    st.caption(f"Fonte: {nome_fonte}")
                    return res
            except Exception as e:
                erros.append(f"{nome_fonte}: {e}")
        raise ConnectionError("Nenhuma fonte de noticias respondeu:\n" + "\n".join(erros))

    def sintetizar(key, nome, noticias):
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
        r.raise_for_status()
        return r.json()["content"][0]["text"]

    def mostrar(alvo, q):
        st.markdown(f"#### {ICON[alvo['status']]} {alvo['nome']} — {alvo['status']}")
        st.caption(f"{alvo['taxa']} | Venc: {alvo['venc']} | {alvo['pl']}% do PL")
        try:
            with st.spinner("Buscando noticias..."):
                noticias = buscar(q)
        except Exception as e:
            st.error(str(e))
            return
        if api_key:
            try:
                with st.spinner("Sintetizando com IA..."):
                    s = sintetizar(api_key, alvo["nome"], noticias)
                st.info(s)
            except Exception as e:
                st.warning(f"Sintese IA falhou: {e}")
        for n in noticias:
            st.markdown(f"- [{n['titulo']}]({n['link']}) `{n['data']}`")

    if btn1:
        mostrar(cri_obj, query)
    elif btn2:
        for alvo in CRIS:
            mostrar(alvo, alvo["query"])
            st.divider()
    else:
        st.info(f"{ICON[cri_obj['status']]} **{cri_obj['nome']}** — {cri_obj['taxa']} | {cri_obj['venc']} | {cri_obj['pl']}% do PL")

# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    label_periodo = {"1mo":"1 mes","3mo":"3 meses","6mo":"6 meses","1y":"1 ano","2y":"2 anos","5y":"5 anos"}
    st.subheader(f"Cotacao IBCR11 — {label_periodo.get(periodo_graf, periodo_graf)}")

    if not cot_ok:
        st.error(f"Cotacao indisponivel:\n```\n{cot_erro}\n```")
    else:
        u = cotacao.iloc[-1]
        m1,m2,m3 = st.columns(3)
        m1.metric("Ultimo fechamento",    f"R$ {u['fechamento']:.2f}")
        m2.metric("Volume ultimo pregao", f"{int(u['volume']):,}" if pd.notna(u["volume"]) else "—")
        if cvm_ok:
            m3.metric("Desagio sobre VP",
                      f"{(1 - u['fechamento']/cvm['vp'])*100:.1f}%",
                      delta_color="inverse",
                      help=f"VP = R${cvm['vp']:.2f} ({cvm['label']})")
        else:
            m3.metric("Desagio sobre VP", "— VP indisponivel")

        fc = go.Figure()
        fc.add_trace(go.Scatter(x=cotacao["data"], y=cotacao["fechamento"],
                                mode="lines", name="Fechamento",
                                line=dict(color="#378ADD", width=2)))
        if cvm_ok:
            fc.add_hline(y=cvm["vp"], line_dash="dash", line_color="#E24B4A",
                         annotation_text=f"VP {cvm['label']} R${cvm['vp']:.2f}")
        fc.update_layout(height=380, yaxis_title="R$", margin=dict(t=20,b=20,l=10,r=130))
        st.plotly_chart(fc, use_container_width=True)

        fv = px.bar(cotacao, x="data", y="volume", title="Volume diario (cotas)",
                    color_discrete_sequence=["#9FE1CB"])
        fv.update_layout(height=200, margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fv, use_container_width=True)

# ── TAB 4 ─────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Stress Test — best / base / worst")
    st.caption("Estimativas de recovery: BREI — Relatorio jan/2026. Atualizar manualmente.")

    df_st = pd.DataFrame([{
        "Ativo":    c["nome"],
        "% PL":     c["pl"],
        "Best %":   c["r_best"],
        "Base %":   c["r_base"],
        "Worst %":  c["r_worst"],
        "HTM Rk":   c["htmk"],
        "Best Rk":  round(c["htmk"] * c["r_best"]  / 100),
        "Base Rk":  round(c["htmk"] * c["r_base"]  / 100),
        "Worst Rk": round(c["htmk"] * c["r_worst"] / 100),
    } for c in CRIS])

    best_mi  = df_st["Best Rk"].sum()  / 1000
    base_mi  = df_st["Base Rk"].sum()  / 1000
    worst_mi = df_st["Worst Rk"].sum() / 1000

    if cvm_ok:
        pl_mi   = cvm["pl_total"] / 1e6
        cotas_n = cvm["cotas"]
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("PL Contabil",  f"R$ {pl_mi:.1f} mi",    f"R$ {cvm['vp']:.2f}/cota ({cvm['label']})")
        k2.metric("PL Best",      f"R$ {best_mi:.1f} mi",  f"R$ {best_mi*1e6/cotas_n:.2f}/cota")
        k3.metric("PL Base",      f"R$ {base_mi:.1f} mi",  f"R$ {base_mi*1e6/cotas_n:.2f}/cota")
        k4.metric("PL Worst",     f"R$ {worst_mi:.1f} mi", f"R$ {worst_mi*1e6/cotas_n:.2f}/cota", delta_color="inverse")
    else:
        st.error(f"PL/VP indisponivel (CVM): {cvm_erro}")
        k2,k3,k4 = st.columns(3)
        k2.metric("PL Best",  f"R$ {best_mi:.1f} mi")
        k3.metric("PL Base",  f"R$ {base_mi:.1f} mi")
        k4.metric("PL Worst", f"R$ {worst_mi:.1f} mi", delta_color="inverse")

    fs = go.Figure()
    nomes = df_st["Ativo"].tolist()
    fs.add_trace(go.Bar(name="Best",  x=nomes, y=df_st["Best Rk"],  marker_color="#1D9E75", opacity=0.6))
    fs.add_trace(go.Bar(name="Base",  x=nomes, y=df_st["Base Rk"],  marker_color="#378ADD"))
    fs.add_trace(go.Bar(name="Worst", x=nomes, y=df_st["Worst Rk"], marker_color="#E24B4A", opacity=0.7))
    fs.update_layout(barmode="group", height=380, yaxis_title="R$ mil",
                     margin=dict(t=10,b=10,l=10,r=10), legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fs, use_container_width=True)
    st.dataframe(df_st, use_container_width=True, hide_index=True)

    st.subheader("IRR esperado — comprado a VM atual")
    vm_ref = cotacao.iloc[-1]["fechamento"] if cot_ok else None
    if vm_ref:
        st.caption(f"Referencia: R$ {vm_ref:.2f}/cota (ultimo fechamento B3)")
    irr = pd.DataFrame([
        ("Positivo", "CRVO + Olimpo resolvidos",         "~20%",       "~R$73/cota", "+49%", "34-38%"),
        ("Base",     "Mercado aceita VP ajustado",        "~25-30%",    "~R$61/cota", "+25%", "23-26%"),
        ("Ruim",     "CRVO 45%, Olimpo piora",            "~40%",       "~R$52/cota", "+6%",  "14-16%"),
        ("Stress",   "Worst case, desagio se mantem 30%", "~30% s/ VP", "~R$40/cota", "-18%", "~0-3%"),
    ], columns=["Cenario","Hipotese","Desagio Final","VM em 24M","Ganho Capital","IRR a.a."])
    st.dataframe(irr, use_container_width=True, hide_index=True)
    st.caption("Cenarios de IRR: estimativa BREI jan/2026. Atualizar manualmente apos novo relatorio.")
