import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="IBCR11 Monitor", page_icon="📊", layout="wide")

TICKER = "IBCR11"

# ── Dados por CRI ─────────────────────────────────────────────────────────────
# queries_noticias: lista de queries para buscar noticias sobre o CRI e o devedor
# queries_cvm: termos para buscar documentos no Fundos.NET da CVM
CRIS = [
    {
        "nome": "CRI CRVO", "status": "CRITICO", "sec": "Riza (ex-Virgo)",
        "taxa": "IPCA+7,00%", "venc": "jun/2036", "pl": 27.3,
        "uf": "RS", "tipo": "BTS", "devedor": "CRVO / Macromix",
        "htmk": 23191.7, "r_best": 80, "r_base": 55, "r_worst": 40,
        "descricao": "BTS para CRVO Madeiras em São Leopoldo/RS. Devedor inadimplente desde 2023. Execução judicial em curso. IBCR11 + outros FIIs como credores. Alienação fiduciária do imóvel em 1ª posição (BB em 2ª).",
        "alertas": ["Inadimplente — execução judicial ativa", "Recovery estimado: 53–58% (base) / 40% (worst)"],
        "queries_noticias": ["CRVO Madeiras Macromix Sao Leopoldo inadimplencia", "CRVO CRI execucao judicial 2025", "Macromix CRVO IBCR11 recuperacao"],
        "queries_cvm": ["CRVO", "Macromix", "Riza CRVO"],
    },
    {
        "nome": "CRI Olimpo", "status": "CRITICO", "sec": "True Securitizadora",
        "taxa": "IPCA+11,00%", "venc": "Vencido jan/2025", "pl": 7.2,
        "uf": "SP", "tipo": "Loteamento", "devedor": "Olimpo / Grupo loteamento SP",
        "htmk": 8570.6, "r_best": 75, "r_base": 65, "r_worst": 50,
        "descricao": "CRI de loteamento vencido em jan/2025. Negociacao extrajudicial em andamento. IBCR11 e KIVO11 como co-holders na mesa de negociacao.",
        "alertas": ["Vencido desde jan/2025 — sem pagamento", "Negociacao extrajudicial com KIVO11"],
        "queries_noticias": ["CRI Olimpo loteamento IBCR11 negociacao", "Olimpo CRI vencido recuperacao 2025", "KIVO11 IBCR11 Olimpo acordo"],
        "queries_cvm": ["Olimpo", "True Securitizadora Olimpo"],
    },
    {
        "nome": "CRI Loft", "status": "ATENCAO", "sec": "Riza (ex-Virgo)",
        "taxa": "IPCA+10,00%", "venc": "jun/2041", "pl": 7.1,
        "uf": "SP", "tipo": "Estoque", "devedor": "Loft / estoque residencial Taubaté",
        "htmk": 11695.4, "r_best": 85, "r_base": 75, "r_worst": 60,
        "descricao": "Estoque de unidades prontas em Taubate/SP. Vendas lentas. Risco de desvalorizacao do estoque se mercado piorar.",
        "alertas": ["Vendas lentas — estoque nao absorvido", "Duration longa: venc. 2041"],
        "queries_noticias": ["Loft CRI Taubate vendas estoqueresidencial", "Loft imobiliario CRI amortizacao 2025"],
        "queries_cvm": ["Loft Taubate CRI", "Riza Loft"],
    },
    {
        "nome": "CRI Pateo II", "status": "ATENCAO", "sec": "Riza (ex-Virgo)",
        "taxa": "IPCA+13,00%", "venc": "jul/2027", "pl": 10.3,
        "uf": "SP", "tipo": "Residencial", "devedor": "Pateo / incorporadora Presidente Prudente",
        "htmk": 8605.4, "r_best": 95, "r_base": 85, "r_worst": 75,
        "descricao": "Empreendimento residencial em Presidente Prudente/SP. Entrega prevista jan-abr/2026. Repasse aos bancos em andamento.",
        "alertas": ["Entrega em jan-abr/2026 — acompanhar repasse"],
        "queries_noticias": ["Pateo Presidente Prudente CRI entrega repasse 2026", "Pateo incorporadora CRI amortizacao"],
        "queries_cvm": ["Pateo CRI Prudente", "Riza Pateo"],
    },
    {
        "nome": "CRI Pateo III", "status": "ATENCAO", "sec": "Riza (ex-Virgo)",
        "taxa": "IPCA+12,50%", "venc": "jul/2027", "pl": 7.6,
        "uf": "SP", "tipo": "Residencial", "devedor": "Pateo / incorporadora Presidente Prudente",
        "htmk": 6446.7, "r_best": 95, "r_base": 85, "r_worst": 75,
        "descricao": "Mesma incorporadora do Pateo II, serie seguinte. Entrega prevista junto com Pateo II.",
        "alertas": ["Entrega em jan-abr/2026 — acompanhar repasse"],
        "queries_noticias": ["Pateo III Presidente Prudente CRI repasse 2026", "Pateo CRI amortizacao serie III"],
        "queries_cvm": ["Pateo III CRI", "Riza Pateo III"],
    },
    {
        "nome": "CRI GDP", "status": "ATENCAO", "sec": "True Securitizadora",
        "taxa": "IPCA+10→12,5%", "venc": "out/2027", "pl": 3.0,
        "uf": "SC", "tipo": "Residencial", "devedor": "Giovanni di Pietro / Joinville",
        "htmk": 2623.6, "r_best": 90, "r_base": 80, "r_worst": 65,
        "descricao": "Empreendimento residencial em Joinville/SC. Pendencia de individualizacao de matriculas. Repasse travado enquanto documentacao nao regularizada.",
        "alertas": ["Individualizacao de matriculas pendente", "Repasse travado por documentacao"],
        "queries_noticias": ["Giovanni di Pietro Joinville CRI individualizacao matriculas", "GDP CRI Joinville repasse regularizacao"],
        "queries_cvm": ["Giovanni Pietro CRI", "True GDP Joinville"],
    },
    {
        "nome": "CRI Villa Res.", "status": "NORMAL", "sec": "True Securitizadora",
        "taxa": "IPCA+9,20%", "venc": "dez/2034", "pl": 8.9,
        "uf": "SC", "tipo": "Residencial", "devedor": "Armona / Villa Residence Itapema",
        "htmk": 8874.8, "r_best": 100, "r_base": 95, "r_worst": 85,
        "descricao": "100% vendido em Itapema/SC. Cash sweep ativo — amortizacoes mensais conforme repasse. Operacao em fase de liquidacao.",
        "alertas": [],
        "queries_noticias": ["Villa Residence Itapema CRI amortizacao repasse", "Armona CRI Itapema liquidacao"],
        "queries_cvm": ["Villa Residence CRI Itapema", "True Villa"],
    },
    {
        "nome": "CRI Braspark", "status": "NORMAL", "sec": "Riza (ex-Virgo)",
        "taxa": "IPCA+8,00%", "venc": "ago/2031", "pl": 6.1,
        "uf": "SC", "tipo": "Logistico", "devedor": "Braspark / galpao logistico Garuva",
        "htmk": 5407.5, "r_best": 100, "r_base": 95, "r_worst": 90,
        "descricao": "Galpao logistico operacional em Garuva/SC. Aluguel R$23/m2. Risco: investigacao CVM sobre Riza (ex-Virgo) como securitizadora.",
        "alertas": ["Atencao: Riza (ex-Virgo) sob investigacao CVM"],
        "queries_noticias": ["Braspark Garuva galpao logistico CRI", "Riza securitizadora CVM investigacao 2025"],
        "queries_cvm": ["Braspark CRI Garuva", "Riza Braspark"],
    },
    {
        "nome": "CRI Vivatti", "status": "NORMAL", "sec": "Riza (ex-Virgo)",
        "taxa": "IPCA+11,00%", "venc": "dez/2029", "pl": 9.0,
        "uf": "SP", "tipo": "Residencial", "devedor": "Vivatti / residencial Presidente Prudente",
        "htmk": 8503.8, "r_best": 100, "r_base": 95, "r_worst": 90,
        "descricao": "Empreendimento residencial em Presidente Prudente/SP. Repasse em curso. Recursos do Maehara sendo direcionados para este CRI.",
        "alertas": [],
        "queries_noticias": ["Vivatti Presidente Prudente CRI repasse 2025", "Vivatti CRI amortizacao Prudente"],
        "queries_cvm": ["Vivatti CRI", "Riza Vivatti"],
    },
    {
        "nome": "CRI Maehara", "status": "NORMAL", "sec": "Riza (ex-Virgo)",
        "taxa": "IPCA+10,00%", "venc": "dez/2031", "pl": 9.8,
        "uf": "SP", "tipo": "Residencial", "devedor": "Maehara / Botanik Presidente Prudente",
        "htmk": 8341.4, "r_best": 100, "r_base": 90, "r_worst": 80,
        "descricao": "Empreendimento Botanik em Presidente Prudente/SP. Vendas em andamento. Recursos sendo transferidos para CRI Vivatti conforme vendas.",
        "alertas": [],
        "queries_noticias": ["Maehara Botanik Presidente Prudente CRI vendas", "Botanik CRI repasse Maehara 2025"],
        "queries_cvm": ["Maehara CRI Botanik", "Riza Maehara"],
    },
    {
        "nome": "CRI Next", "status": "NORMAL", "sec": "True Securitizadora",
        "taxa": "IPCA+12,50%", "venc": "out/2027", "pl": 0.1,
        "uf": "ES", "tipo": "Residencial", "devedor": "Next / residencial Serra-ES",
        "htmk": 105.2, "r_best": 100, "r_base": 100, "r_worst": 90,
        "descricao": "Obras 100% concluidas em Serra/ES. Vendas 69%. Amortizacao praticamente total ja realizada.",
        "alertas": [],
        "queries_noticias": ["CRI Next Serra Espirito Santo obras vendas", "Next CRI ES amortizacao residencial"],
        "queries_cvm": ["Next CRI Serra ES", "True Next"],
    },
]

ICON = {"CRITICO": "🔴", "ATENCAO": "🟡", "NORMAL": "🟢"}
COR  = {"CRITICO": "#E24B4A", "ATENCAO": "#EF9F27", "NORMAL": "#1D9E75"}
HEADERS_WEB = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

# ── Yahoo Finance ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def get_cotacao(periodo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}.SA?interval=1d&range={periodo}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    result = r.json()["chart"]["result"]
    if not result:
        raise ValueError(f"Yahoo Finance sem dados para {TICKER}.SA")
    d  = result[0]
    df = pd.DataFrame({
        "data":       [datetime.fromtimestamp(t).strftime("%Y-%m-%d") for t in d["timestamp"]],
        "fechamento": d["indicators"]["quote"][0]["close"],
        "volume":     d["indicators"]["quote"][0]["volume"],
    }).dropna(subset=["fechamento"])
    return df

# ── Yahoo Finance: fundamentais (VP, P/VP, DY) ───────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_fundamentais():
    """
    Yahoo Finance v10 quoteSummary retorna dados fundamentais incluindo
    bookValue (VP/cota), priceToBook (P/VP) e dividendYield para FIIs.
    """
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{TICKER}.SA"
    params = {"modules": "defaultKeyStatistics,summaryDetail,price"}
    r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    data = r.json()

    if "quoteSummary" not in data or data["quoteSummary"].get("error"):
        raise ValueError(f"Yahoo Finance quoteSummary erro: {data}")

    result = data["quoteSummary"]["result"]
    if not result:
        raise ValueError("Yahoo Finance quoteSummary: resultado vazio")

    ks  = result[0].get("defaultKeyStatistics", {})
    sd  = result[0].get("summaryDetail", {})
    pr  = result[0].get("price", {})

    def raw(d, key):
        v = d.get(key, {})
        if isinstance(v, dict):
            return v.get("raw")
        return v

    vp  = raw(ks, "bookValue")
    pvp = raw(ks, "priceToBook")
    dy  = raw(sd, "dividendYield")
    mc  = raw(pr, "marketCap")

    if dy and dy < 1:   # Yahoo retorna como decimal (0.15 = 15%)
        dy = round(dy * 100, 2)

    resultado = {}
    if vp:  resultado["vp"]      = vp
    if pvp: resultado["pvp"]     = pvp
    if dy:  resultado["dy_12m"]  = dy
    if mc:  resultado["market_cap"] = mc

    if not resultado:
        raise ValueError(
            f"Yahoo Finance: nenhum campo fundamental retornado.\n"
            f"defaultKeyStatistics keys: {list(ks.keys())}\n"
            f"summaryDetail keys: {list(sd.keys())}"
        )
    return resultado

# ── Noticias RSS ──────────────────────────────────────────────────────────────
def buscar_noticias(query: str, max_items: int = 5):
    fontes = [
        ("Google News", f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"),
        ("Bing News",   f"https://www.bing.com/news/search?q={requests.utils.quote(query)}&format=rss"),
    ]
    for nome_fonte, url in fontes:
        try:
            r    = requests.get(url, headers=HEADERS_WEB, timeout=10)
            soup = BeautifulSoup(r.content, "html.parser")
            items = soup.find_all("item")
            if items:
                return nome_fonte, [
                    {"titulo": i.find("title").text if i.find("title") else "",
                     "link":   i.find("link").text  if i.find("link")  else "",
                     "data":   i.find("pubdate").text[:16] if i.find("pubdate") else ""}
                    for i in items[:max_items]
                ]
        except:
            continue
    return None, []

# ── Documentos CVM (Fundos.NET) ───────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def buscar_docs_cvm(query: str):
    url = "https://fnet.bmfbovespa.com.br/fnet/publico/pesquisarGerenciadorDocumentosDados"
    params = {
        "d": 0, "s": 0, "l": 8, "o[0][dt_entrega]": "desc",
        "tipoParticipante": 2,  # 2 = securitizadora/emissora
        "certificado": query,
        "situacao": "A",
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS_WEB, timeout=10)
        r.raise_for_status()
        data = r.json()
        docs = data.get("data", [])
        return [{"titulo": d.get("nm_tipo_documento",""),
                 "data":   d.get("dt_entrega","")[:10],
                 "link":   f"https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id={d.get('id_documento','')}",
                 "emissor": d.get("nm_emissor","")}
                for d in docs if d.get("id_documento")]
    except Exception as e:
        return []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("IBCR11 Monitor")
    periodo_graf = st.select_slider("Historico B3",
                                    options=["1mo","3mo","6mo","1y","2y","5y"],
                                    value="3mo")
    st.divider()
    filtro_status = st.multiselect("Filtrar CRIs", ["CRITICO","ATENCAO","NORMAL"],
                                   default=["CRITICO","ATENCAO","NORMAL"])
    st.divider()
    api_key = st.text_input("Anthropic API Key (opcional)", type="password")
    st.divider()
    if st.button("Limpar cache"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Yahoo Finance (cotacao + fundamentais) + CVM Fundos.NET")

# ── Carrega dados do fundo ────────────────────────────────────────────────────
cot_ok, cotacao, cot_erro = False, None, None
try:
    with st.spinner("Carregando cotacao..."):
        cotacao = get_cotacao(periodo_graf)
    cot_ok = True
except Exception as e:
    cot_erro = str(e)

si_ok, si, si_erro = False, None, None
try:
    with st.spinner("Carregando fundamentais..."):
        si = get_fundamentais()
    si_ok = True
except Exception as e:
    si_erro = str(e)

vm  = cotacao.iloc[-1]["fechamento"] if cot_ok else None
vp  = si.get("vp")  if si_ok else None
pvp = si.get("pvp") if si_ok else None
dy  = si.get("dy_12m") if si_ok else None
desagio = round((1 - vm / vp) * 100, 2) if vm and vp else None

# ── Header ────────────────────────────────────────────────────────────────────
st.title("IBCR11 — Monitor de Carteira")

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("VM/cota", f"R$ {vm:.2f}" if vm else "— erro")
c2.metric("VP/cota", f"R$ {vp:.2f}" if vp else "— erro")
c3.metric("P/VP",    f"{pvp:.2f}x"  if pvp else "—")
c4.metric("Desagio", f"{desagio:.1f}%" if desagio else "—", delta_color="inverse")
c5.metric("DY 12m",  f"{dy:.2f}%"   if dy else "—")

erros = []
if not cot_ok: erros.append(f"Yahoo Finance: {cot_erro}")
if not si_ok:  erros.append(f"Fundamentais Yahoo Finance: {si_erro}")
if erros:
    with st.expander("Erros de carregamento"):
        for e in erros: st.error(e)

st.divider()

# ── Tabs principais ───────────────────────────────────────────────────────────
tab_geral, tab_cri, tab_fundo = st.tabs(["Visao Geral", "Painel por CRI", "Cotacao & Fundo"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB: VISAO GERAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_geral:
    cris_f = [c for c in CRIS if c["status"] in filtro_status]

    # Cards de alerta por CRI
    st.subheader("Status da Carteira")
    cols = st.columns(3)
    for i, cri in enumerate(cris_f):
        with cols[i % 3]:
            cor_borda = COR[cri["status"]]
            alertas_txt = "\n".join(f"• {a}" for a in cri["alertas"]) if cri["alertas"] else "Sem alertas ativos"
            st.markdown(f"""
<div style="border-left: 4px solid {cor_borda}; padding: 10px 14px; margin-bottom: 12px; border-radius: 4px; background: rgba(255,255,255,0.03)">
<b>{ICON[cri['status']]} {cri['nome']}</b><br>
<small>{cri['devedor']} | {cri['sec']}</small><br>
<small>{cri['taxa']} | Venc: {cri['venc']} | {cri['pl']}% PL</small><br>
<small style="color:{cor_borda}">{alertas_txt}</small>
</div>""", unsafe_allow_html=True)

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Composicao por status (% PL)")
        df_pie = pd.DataFrame([{"Status": s, "PL": sum(c["pl"] for c in CRIS if c["status"] == s)}
                                for s in ["CRITICO","ATENCAO","NORMAL"]])
        fig1 = px.pie(df_pie, names="Status", values="PL", color="Status",
                      color_discrete_map=COR, hole=0.4)
        fig1.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig1, use_container_width=True)
    with col_b:
        st.subheader("Recovery base vs HTM (R$ mil)")
        df_rec = pd.DataFrame([{
            "CRI":      c["nome"],
            "HTM":      c["htmk"],
            "Recovery": round(c["htmk"] * c["r_base"] / 100),
            "Perda":    round(c["htmk"] * (1 - c["r_base"] / 100)),
        } for c in CRIS]).sort_values("HTM", ascending=True)
        fig_rec = go.Figure()
        fig_rec.add_trace(go.Bar(name="Recovery", x=df_rec["CRI"], y=df_rec["Recovery"], marker_color="#1D9E75"))
        fig_rec.add_trace(go.Bar(name="Perda est.", x=df_rec["CRI"], y=df_rec["Perda"], marker_color="#E24B4A", opacity=0.7))
        fig_rec.update_layout(barmode="stack", height=300, margin=dict(t=10,b=10,l=10,r=10),
                              legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_rec, use_container_width=True)

    st.subheader("Tabela resumo")
    df_t = pd.DataFrame([{
        "": ICON[c["status"]], "CRI": c["nome"], "Status": c["status"],
        "Devedor": c["devedor"], "Sec": c["sec"],
        "% PL": c["pl"], "Taxa": c["taxa"], "Venc": c["venc"],
        "HTM Rk": c["htmk"], "Best%": c["r_best"], "Base%": c["r_base"], "Worst%": c["r_worst"],
    } for c in cris_f])
    st.dataframe(df_t, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB: PAINEL POR CRI
# ══════════════════════════════════════════════════════════════════════════════
with tab_cri:
    # Selector de CRI
    cri_names = [f"{ICON[c['status']]} {c['nome']}" for c in CRIS]
    cri_sel   = st.selectbox("Selecionar CRI", cri_names)
    cri       = next(c for c in CRIS if c["nome"] in cri_sel)

    cor = COR[cri["status"]]
    st.markdown(f"""
<div style="border-left: 5px solid {cor}; padding: 12px 18px; border-radius: 6px; background: rgba(255,255,255,0.03); margin-bottom: 16px">
<h3 style="margin:0">{ICON[cri['status']]} {cri['nome']} — {cri['status']}</h3>
<p style="margin:4px 0; opacity:0.8">{cri['devedor']} &nbsp;|&nbsp; Securitizadora: {cri['sec']}</p>
<p style="margin:4px 0; opacity:0.8">{cri['taxa']} &nbsp;|&nbsp; Venc: {cri['venc']} &nbsp;|&nbsp; {cri['pl']}% do PL &nbsp;|&nbsp; HTM: R$ {cri['htmk']:,.0f}k &nbsp;|&nbsp; {cri['uf']}</p>
</div>""", unsafe_allow_html=True)

    # Alertas
    if cri["alertas"]:
        for alerta in cri["alertas"]:
            st.warning(f"⚠️ {alerta}")

    # Descricao
    st.info(cri["descricao"])

    # KPIs de recovery
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("HTM (R$ mil)",   f"R$ {cri['htmk']:,.0f}k")
    k2.metric("Recovery Best",  f"{cri['r_best']}% — R$ {cri['htmk']*cri['r_best']/100:,.0f}k")
    k3.metric("Recovery Base",  f"{cri['r_base']}% — R$ {cri['htmk']*cri['r_base']/100:,.0f}k")
    k4.metric("Recovery Worst", f"{cri['r_worst']}% — R$ {cri['htmk']*cri['r_worst']/100:,.0f}k",
              delta_color="inverse")

    st.divider()

    # 4 dimensoes em sub-tabs
    sub1, sub2, sub3, sub4 = st.tabs(["Noticias", "Docs CVM", "Juridico / Status", "Financeiro"])

    # ── Sub-tab: Noticias ─────────────────────────────────────────────────────
    with sub1:
        st.subheader("Noticias recentes")
        query_edit = st.text_input("Query de busca", value=cri["queries_noticias"][0], key=f"q_{cri['nome']}")
        col_b1, col_b2, col_b3, _ = st.columns([1,1,1,4])
        btn_buscar   = col_b1.button("Buscar", type="primary", key=f"btn1_{cri['nome']}")
        btn_alternativas = col_b2.button("Queries alternativas", key=f"btn2_{cri['nome']}")
        btn_sintetizar   = col_b3.button("Sintetizar com IA", key=f"btn3_{cri['nome']}", disabled=not api_key)

        if btn_buscar or btn_alternativas:
            queries = [query_edit] if btn_buscar else cri["queries_noticias"]
            all_noticias = []
            for q in queries:
                fonte, noticias = buscar_noticias(q)
                if noticias:
                    st.caption(f"Fonte: {fonte} | Query: `{q}`")
                    for n in noticias:
                        st.markdown(f"- [{n['titulo']}]({n['link']}) `{n['data']}`")
                    all_noticias.extend(noticias)
                else:
                    st.warning(f"Sem resultados para: `{q}`")

            if btn_sintetizar and all_noticias and api_key:
                textos = "\n".join(f"- {n['titulo']}" for n in all_noticias[:10])
                try:
                    with st.spinner("Sintetizando..."):
                        r = requests.post(
                            "https://api.anthropic.com/v1/messages",
                            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                                     "content-type": "application/json"},
                            json={"model": "claude-sonnet-4-20250514", "max_tokens": 300,
                                  "messages": [{"role": "user", "content":
                                      f"Voce e um analista de credito imobiliario. Sintetize em 3-4 frases "
                                      f"as novidades sobre o {cri['nome']} (devedor: {cri['devedor']}, "
                                      f"securitizadora: {cri['sec']}). Status atual: {cri['status']}. "
                                      f"Diga se o risco melhorou, piorou ou esta estavel e por que.\n\n{textos}"}]},
                            timeout=20
                        )
                        r.raise_for_status()
                        st.success(r.json()["content"][0]["text"])
                except Exception as e:
                    st.error(f"Erro IA: {e}")
        else:
            st.caption(f"Queries disponiveis: {' | '.join(cri['queries_noticias'])}")
            st.info("Clique em 'Buscar' para carregar noticias.")

        if btn_sintetizar and not btn_buscar and not btn_alternativas:
            st.warning("Clique em 'Buscar' primeiro para carregar noticias, depois 'Sintetizar com IA'.")

    # ── Sub-tab: Docs CVM ─────────────────────────────────────────────────────
    with sub2:
        st.subheader("Documentos CVM (Fundos.NET)")
        query_cvm = st.selectbox("Buscar por", cri["queries_cvm"], key=f"qcvm_{cri['nome']}")
        if st.button("Buscar documentos CVM", key=f"btncvm_{cri['nome']}"):
            with st.spinner("Consultando CVM..."):
                docs = buscar_docs_cvm(query_cvm)
            if not docs:
                st.warning(f"Nenhum documento encontrado para '{query_cvm}' no Fundos.NET.")
                st.caption("Tente buscar diretamente em: https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM")
            else:
                df_docs = pd.DataFrame(docs)
                st.dataframe(df_docs, use_container_width=True, hide_index=True)
                st.caption(f"{len(docs)} documentos encontrados")
        else:
            st.info("Clique para buscar documentos publicados pela securitizadora na CVM.")
            st.caption(f"Link direto CVM: https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM")

    # ── Sub-tab: Juridico / Status ────────────────────────────────────────────
    with sub3:
        st.subheader("Status juridico e operacional")
        st.caption("Atualizacao manual — preencher apos cada relatorio mensal do BREI")

        status_options = ["Normal — pagando em dia", "Em negociacao", "Inadimplente — execucao extrajudicial",
                          "Inadimplente — execucao judicial", "Vencido — aguardando liquidacao", "Liquidado"]
        status_atual = {"CRITICO": status_options[3], "ATENCAO": status_options[1], "NORMAL": status_options[0]}

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Status juridico", status_options,
                         index=status_options.index(status_atual[cri["status"]]),
                         key=f"status_jur_{cri['nome']}")
            st.text_area("Resumo da situacao juridica", value=cri["descricao"],
                         height=120, key=f"resumo_jur_{cri['nome']}")
        with col2:
            st.text_area("Ultimas acoes do gestor (BREI)",
                         placeholder="ex: 25/jan/26 — BREI contratou escritorio X para execucao do imovel...",
                         height=120, key=f"acoes_gestor_{cri['nome']}")
            st.text_input("Proximo evento esperado",
                          placeholder="ex: Leilao do imovel previsto para mar/2026",
                          key=f"proximo_evento_{cri['nome']}")

        st.info("Estes campos sao apenas para referencia visual — nao sao salvos entre sessoes. Para persistir, use um arquivo de notas externo ou implemente persistencia no banco de dados.")

    # ── Sub-tab: Financeiro ───────────────────────────────────────────────────
    with sub4:
        st.subheader("Dados financeiros")
        st.caption("Atualizar mensalmente com base no relatorio do BREI e informe da securitizadora")

        col1, col2 = st.columns(2)
        with col1:
            st.number_input("HTM atual (R$ mil)", value=float(cri["htmk"]),
                            key=f"htm_{cri['nome']}", step=10.0)
            st.number_input("Recovery estimado base (%)", value=float(cri["r_base"]),
                            min_value=0.0, max_value=100.0, key=f"rec_{cri['nome']}", step=1.0)
            st.text_input("Ultima amortizacao", placeholder="ex: R$ 250k em dez/2025",
                          key=f"amort_{cri['nome']}")
        with col2:
            st.number_input("Taxa atual (IPCA+)", value=float(cri["taxa"].replace("IPCA+","").replace("%","").replace("→12,5","").replace("10-12,5","10") or 10),
                            key=f"taxa_{cri['nome']}", step=0.25)
            st.text_input("Saldo devedor aproximado", placeholder="ex: R$ 18,5 mi (nov/2025)",
                          key=f"saldo_{cri['nome']}")
            st.text_input("Garantias", placeholder="ex: AF imovel R$ 28mi + aval pessoal",
                          key=f"garantias_{cri['nome']}")

        # Grafico de cenarios de recovery
        fig_sc = go.Figure()
        fig_sc.add_trace(go.Bar(
            x=["Worst", "Base", "Best"],
            y=[cri["htmk"]*cri["r_worst"]/100, cri["htmk"]*cri["r_base"]/100, cri["htmk"]*cri["r_best"]/100],
            marker_color=["#E24B4A", "#378ADD", "#1D9E75"],
            text=[f"R$ {cri['htmk']*cri['r_worst']/100:,.0f}k", f"R$ {cri['htmk']*cri['r_base']/100:,.0f}k", f"R$ {cri['htmk']*cri['r_best']/100:,.0f}k"],
            textposition="outside"
        ))
        fig_sc.add_hline(y=cri["htmk"], line_dash="dash", line_color="gray", annotation_text=f"HTM R${cri['htmk']:,.0f}k")
        fig_sc.update_layout(height=280, yaxis_title="R$ mil", showlegend=False,
                             margin=dict(t=30,b=10,l=10,r=10))
        st.plotly_chart(fig_sc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB: COTACAO & FUNDO
# ══════════════════════════════════════════════════════════════════════════════
with tab_fundo:
    label_p = {"1mo":"1 mes","3mo":"3 meses","6mo":"6 meses","1y":"1 ano","2y":"2 anos","5y":"5 anos"}
    st.subheader(f"Cotacao IBCR11 — {label_p.get(periodo_graf, periodo_graf)}")

    if not cot_ok:
        st.error(f"Cotacao indisponivel: {cot_erro}")
    else:
        u = cotacao.iloc[-1]
        m1,m2,m3 = st.columns(3)
        m1.metric("Ultimo fechamento",    f"R$ {u['fechamento']:.2f}")
        m2.metric("Volume ultimo pregao", f"{int(u['volume']):,}" if pd.notna(u["volume"]) else "—")
        m3.metric("Desagio sobre VP",     f"{desagio:.1f}%" if desagio else "—", delta_color="inverse")

        fc = go.Figure()
        fc.add_trace(go.Scatter(x=cotacao["data"], y=cotacao["fechamento"],
                                mode="lines", name="Fechamento", line=dict(color="#378ADD", width=2)))
        if vp:
            fc.add_hline(y=vp, line_dash="dash", line_color="#E24B4A", annotation_text=f"VP R${vp:.2f}")
        fc.update_layout(height=380, yaxis_title="R$", margin=dict(t=20,b=20,l=10,r=120))
        st.plotly_chart(fc, use_container_width=True)

        fv = px.bar(cotacao, x="data", y="volume", title="Volume diario",
                    color_discrete_sequence=["#9FE1CB"])
        fv.update_layout(height=200, margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fv, use_container_width=True)

    st.divider()
    st.subheader("Stress test — carteira consolidada")
    df_st = pd.DataFrame([{
        "CRI": c["nome"], "% PL": c["pl"], "HTM": c["htmk"],
        "Best": round(c["htmk"]*c["r_best"]/100), "Base": round(c["htmk"]*c["r_base"]/100),
        "Worst": round(c["htmk"]*c["r_worst"]/100),
    } for c in CRIS])
    s1,s2,s3 = st.columns(3)
    s1.metric("PL Best",  f"R$ {df_st['Best'].sum()/1000:.1f} mi")
    s2.metric("PL Base",  f"R$ {df_st['Base'].sum()/1000:.1f} mi")
    s3.metric("PL Worst", f"R$ {df_st['Worst'].sum()/1000:.1f} mi", delta_color="inverse")
    fs = go.Figure()
    fs.add_trace(go.Bar(name="Best",  x=df_st["CRI"], y=df_st["Best"],  marker_color="#1D9E75", opacity=0.6))
    fs.add_trace(go.Bar(name="Base",  x=df_st["CRI"], y=df_st["Base"],  marker_color="#378ADD"))
    fs.add_trace(go.Bar(name="Worst", x=df_st["CRI"], y=df_st["Worst"], marker_color="#E24B4A", opacity=0.7))
    fs.update_layout(barmode="group", height=350, yaxis_title="R$ mil",
                     margin=dict(t=10,b=10,l=10,r=10), legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fs, use_container_width=True)
    st.caption("Recovery: estimativas BREI jan/2026.")
