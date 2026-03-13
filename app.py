import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import plotly.graph_objects as go

st.set_page_config(page_title="IBCR11 Monitor", page_icon="📊", layout="wide")

TICKER = "IBCR11"

CRIS = [
    {"nome": "CRI CRVO",       "status": "CRITICO",  "pl": 27.3, "taxa": "IPCA+7,00%",    "venc": "jun/2036", "devedor": "CRVO / Macromix",          "sec": "Riza",  "r_base": 55,  "htmk": 23191.7, "alerta": "Inadimplente — execucao judicial ativa",          "queries": ["CRVO Macromix inadimplencia execucao", "CRVO CRI IBCR11 2025"]},
    {"nome": "CRI Olimpo",     "status": "CRITICO",  "pl": 7.2,  "taxa": "IPCA+11,00%",   "venc": "Vencido",  "devedor": "Olimpo loteamento",        "sec": "True",  "r_base": 65,  "htmk": 8570.6,  "alerta": "Vencido jan/2025 — negociacao extrajudicial",     "queries": ["Olimpo CRI vencido negociacao IBCR11", "KIVO11 Olimpo acordo 2025"]},
    {"nome": "CRI Loft",       "status": "ATENCAO",  "pl": 7.1,  "taxa": "IPCA+10,00%",   "venc": "jun/2041", "devedor": "Loft / estoque Taubate",    "sec": "Riza",  "r_base": 75,  "htmk": 11695.4, "alerta": "Vendas lentas — estoque nao absorvido",           "queries": ["Loft CRI Taubate estoque vendas 2025"]},
    {"nome": "CRI Pateo II",   "status": "ATENCAO",  "pl": 10.3, "taxa": "IPCA+13,00%",   "venc": "jul/2027", "devedor": "Pateo / Pres. Prudente",    "sec": "Riza",  "r_base": 85,  "htmk": 8605.4,  "alerta": "Entrega jan-abr/2026 — acompanhar repasse",       "queries": ["Pateo Presidente Prudente CRI entrega repasse 2026"]},
    {"nome": "CRI Pateo III",  "status": "ATENCAO",  "pl": 7.6,  "taxa": "IPCA+12,50%",   "venc": "jul/2027", "devedor": "Pateo / Pres. Prudente",    "sec": "Riza",  "r_base": 85,  "htmk": 6446.7,  "alerta": "Entrega jan-abr/2026 — acompanhar repasse",       "queries": ["Pateo III CRI amortizacao repasse 2026"]},
    {"nome": "CRI GDP",        "status": "ATENCAO",  "pl": 3.0,  "taxa": "IPCA+10-12,5%", "venc": "out/2027", "devedor": "Giovanni di Pietro SC",     "sec": "True",  "r_base": 80,  "htmk": 2623.6,  "alerta": "Matriculas pendentes — repasse travado",          "queries": ["Giovanni Pietro Joinville CRI matriculas repasse"]},
    {"nome": "CRI Villa Res.", "status": "NORMAL",   "pl": 8.9,  "taxa": "IPCA+9,20%",    "venc": "dez/2034", "devedor": "Armona / Itapema SC",       "sec": "True",  "r_base": 95,  "htmk": 8874.8,  "alerta": "",                                                "queries": ["Villa Residence Itapema CRI amortizacao"]},
    {"nome": "CRI Braspark",   "status": "NORMAL",   "pl": 6.1,  "taxa": "IPCA+8,00%",    "venc": "ago/2031", "devedor": "Braspark / Garuva SC",      "sec": "Riza",  "r_base": 95,  "htmk": 5407.5,  "alerta": "Sec. Riza sob investigacao CVM",                  "queries": ["Braspark Garuva galpao CRI", "Riza securitizadora CVM investigacao"]},
    {"nome": "CRI Vivatti",    "status": "NORMAL",   "pl": 9.0,  "taxa": "IPCA+11,00%",   "venc": "dez/2029", "devedor": "Vivatti / Pres. Prudente",  "sec": "Riza",  "r_base": 95,  "htmk": 8503.8,  "alerta": "",                                                "queries": ["Vivatti Presidente Prudente CRI repasse 2025"]},
    {"nome": "CRI Maehara",    "status": "NORMAL",   "pl": 9.8,  "taxa": "IPCA+10,00%",   "venc": "dez/2031", "devedor": "Maehara / Botanik SP",      "sec": "Riza",  "r_base": 90,  "htmk": 8341.4,  "alerta": "",                                                "queries": ["Maehara Botanik Presidente Prudente CRI vendas"]},
    {"nome": "CRI Next",       "status": "NORMAL",   "pl": 0.1,  "taxa": "IPCA+12,50%",   "venc": "out/2027", "devedor": "Next / Serra ES",           "sec": "True",  "r_base": 100, "htmk": 105.2,   "alerta": "",                                                "queries": ["Next CRI Serra Espirito Santo obras"]},
]

ICON = {"CRITICO": "🔴", "ATENCAO": "🟡", "NORMAL": "🟢"}
COR  = {"CRITICO": "#E24B4A", "ATENCAO": "#EF9F27", "NORMAL": "#1D9E75"}

# ── Data fetching ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def get_cotacao():
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}.SA?interval=1d&range=6mo"
    r   = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    return pd.DataFrame({
        "data":  [datetime.fromtimestamp(t).strftime("%Y-%m-%d") for t in res["timestamp"]],
        "preco": res["indicators"]["quote"][0]["close"],
        "vol":   res["indicators"]["quote"][0]["volume"],
    }).dropna(subset=["preco"])

@st.cache_data(ttl=3600, show_spinner=False)
def get_fundamentais():
    """
    Obtém VP, P/VP e DY do IBCR11. Cascata de fontes:

      1. Clube FII /fundo_basico (AJAX GET, HTML parcial com #primaryTable)
         Confirmado 200 OK no DevTools. Requer sessão com cookies Cloudflare.
         Estratégia: abre sessão na homepage primeiro para obter cf_clearance,
         depois chama /fundo_basico simulando exatamente o que o browser faz.

      2. Clube FII /pega_cotacao (POST) para cotação tempo-real
         Retorna texto puro: "51,00;13/03/2026 17:26:42;0,00"
         Usado como complemento ao fundo_basico se VP/DY já vieram.

      3. Fundamentus — fallback externo sem Cloudflare
    """
    import re, time

    NUM_COTAS = 958_423

    # Headers que replicam exatamente o que o browser envia (confirmado no DevTools)
    UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
    BASE_HEADERS = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
    }

    def parse_br(txt):
        t = str(txt).strip().replace("R$","").replace("%","").replace("\xa0","").strip()
        t = t.replace(".","").replace(",",".")
        return float(t)

    def parse_primary_table(html):
        """Lê #primaryTable e retorna dict com VP, PVP, DY, cotistas, liquidez."""
        soup  = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"id": "primaryTable"})
        if not table:
            return {}
        res = {}
        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            label = th.get_text(" ", strip=True).upper()
            valor = td.get_text(" ", strip=True)
            try:
                if "P/VP" in label:
                    res["pvp"] = parse_br(valor)
                elif "VALOR PATRIMONIAL" in label:
                    res["vp_total"] = parse_br(valor)
                    res["vp"] = round(res["vp_total"] / NUM_COTAS, 2)
                elif "DIVIDEND YIELD" in label:
                    # Célula: "1,18% e \n 17,43%"
                    partes = valor.replace("%","").split("e")
                    if len(partes) >= 1:
                        res["dy_ultimo"] = parse_br(partes[0])
                    if len(partes) >= 2:
                        res["dy_12m"] = parse_br(partes[1])
                elif "COTISTAS" in label:
                    res["cotistas"] = int(parse_br(valor))
                elif "LIQUIDEZ" in label:
                    res["liquidez"] = parse_br(valor)
            except Exception:
                pass
        # VP/cota também aparece no bloco .progress — mais preciso que calcular
        if not res.get("vp"):
            soup2 = BeautifulSoup(html, "html.parser")
            for strong in soup2.find_all("strong"):
                if "patrimonial por cota" in strong.get_text("", strip=True).lower():
                    prog = strong.find_next("div", class_="progress")
                    if prog:
                        span = prog.find("span")
                        if span:
                            try:
                                res["vp"] = parse_br(span.get_text())
                                break
                            except Exception:
                                pass
        return res

    erros = []

    # ── 1. Clube FII — AJAX /fundo_basico ─────────────────────────────────────
    # Confirmado 200 OK no DevTools. O browser:
    #   a) visita a homepage para receber os cookies Cloudflare (cf_clearance)
    #   b) depois chama GET /fundo_basico com X-Requested-With: XMLHttpRequest
    # requests.Session() propaga os cookies automaticamente entre as chamadas.
    try:
        sess = requests.Session()
        sess.headers.update(BASE_HEADERS)

        # Passo a: homepage → obtém cookies de sessão (ASP.NET_SessionId, cf_clearance)
        sess.get("https://www.clubefii.com.br/", timeout=12)
        time.sleep(0.5)  # pequena pausa, igual browser

        # Passo b: chama o endpoint AJAX exatamente como o jQuery faz
        r = sess.get(
            f"https://www.clubefii.com.br/fundo_basico?cod={TICKER}&fiiLiberado=False",
            headers={
                "Referer": f"https://www.clubefii.com.br/fiis/{TICKER}",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "text/html, */*; q=0.01",
            },
            timeout=20,
        )
        r.raise_for_status()

        res = parse_primary_table(r.text)
        if res.get("vp") or res.get("pvp"):
            # Bônus: busca cotação tempo-real via /pega_cotacao (POST simples)
            try:
                rc = sess.post(
                    "https://www.clubefii.com.br/pega_cotacao",
                    data={"cod_neg": TICKER},
                    headers={"Referer": f"https://www.clubefii.com.br/fiis/{TICKER}",
                             "Content-Type": "application/x-www-form-urlencoded"},
                    timeout=8,
                )
                partes = rc.text.strip().split(";")
                # resposta: "51,00;13/03/2026 17:26:42;0,00"
                if len(partes) >= 1:
                    res["vm_rt"] = parse_br(partes[0])   # cotação tempo-real
                if len(partes) >= 3:
                    res["var_rt"] = parse_br(partes[2])  # variação %
            except Exception:
                pass  # cotação RT é bônus, não bloqueia

            res["_fonte"] = "Clube FII AJAX"
            return res

        erros.append(f"fundo_basico: HTML retornado sem #primaryTable útil")

    except Exception as e:
        erros.append(f"fundo_basico: {e}")

    # ── 2. Clube FII — página principal completa ──────────────────────────────
    # Fallback: carrega a página toda. Mais pesado mas traz o mesmo #primaryTable.
    try:
        sess = requests.Session()
        sess.headers.update(BASE_HEADERS)
        sess.get("https://www.clubefii.com.br/", timeout=12)
        time.sleep(0.8)

        r = sess.get(
            f"https://www.clubefii.com.br/fiis/{TICKER}",
            headers={"Referer": "https://www.clubefii.com.br/fundo_imobiliario_lista"},
            timeout=25,
        )
        r.raise_for_status()

        res = parse_primary_table(r.text)

        # Extrai também variáveis JS inline (embutidas no <script> da página)
        m = re.search(r"it_val_ultimo_rendimento\s*=\s*([\d.]+)", r.text)
        if m:
            try:
                res["ultimo_rendimento"] = float(m.group(1))
            except Exception:
                pass

        if res.get("vp") or res.get("pvp"):
            res["_fonte"] = "Clube FII (página)"
            return res

        erros.append("Página principal: Cloudflare bloqueou ou primaryTable vazia")

    except Exception as e:
        erros.append(f"Página principal: {e}")

    # ── 3. Fundamentus ────────────────────────────────────────────────────────
    try:
        r = requests.get(
            f"https://www.fundamentus.com.br/fii_detalhes.php?papel={TICKER}",
            headers={**BASE_HEADERS, "Referer": "https://www.fundamentus.com.br/"},
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        res  = {}
        for row in soup.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            for i, cell in enumerate(cells):
                if i + 1 >= len(cells):
                    continue
                cu  = cell.upper()
                val = cells[i + 1]
                try:
                    if any(x in cu for x in ("VP/COTA", "VPA", "VAL. PATR./COTA")):
                        res["vp"] = parse_br(val)
                    elif cu in ("P/VP", "P/VPA"):
                        res["pvp"] = parse_br(val)
                    elif "DY" in cu and "12" in cu:
                        res["dy_12m"] = parse_br(val)
                except Exception:
                    pass
        if res.get("vp") or res.get("pvp"):
            res["_fonte"] = "Fundamentus"
            return res
        erros.append("Fundamentus: campos não encontrados na página")

    except Exception as e:
        erros.append(f"Fundamentus: {e}")

    raise ConnectionError(
        "Todas as fontes falharam:\n" + "\n".join(f"  • {e}" for e in erros)
    )


def buscar_noticias(query):
    for url in [
        f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=pt-BR&gl=BR&ceid=BR:pt-419",
        f"https://www.bing.com/news/search?q={requests.utils.quote(query)}&format=rss",
    ]:
        try:
            r    = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            soup = BeautifulSoup(r.content, "html.parser")
            items = soup.find_all("item")
            if items:
                return [{"t": i.find("title").text, "l": i.find("link").text,
                         "d": i.find("pubdate").text[:16] if i.find("pubdate") else ""}
                        for i in items[:5]]
        except:
            continue
    return []

# ── Load ──────────────────────────────────────────────────────────────────────
st.title("IBCR11 — Monitor")

try:
    with st.spinner("Carregando cotacao..."):
        df_hist = get_cotacao()
    vm = df_hist.iloc[-1]["preco"]
    try:
        with st.spinner("Buscando VP/DY..."):
            fund = get_fundamentais()
        vp     = fund.get("vp")
        pvp    = fund.get("pvp") or (round(vm/vp, 2) if vm and vp else None)
        dy     = fund.get("dy_12m") or fund.get("dy_ultimo")
        dy_ult = fund.get("dy_ultimo")
        fonte  = fund.get("_fonte", "desconhecida")
        st.sidebar.success(f"✅ Dados via {fonte}")
    except Exception as ef:
        vp     = st.session_state.get("vp_manual")
        dy     = st.session_state.get("dy_manual")
        dy_ult = None
        pvp    = round(vm/vp, 2) if vm and vp else None
        st.sidebar.warning(f"⚠️ Scraping falhou — valores manuais\n\n{str(ef)[:200]}")
    pvp = pvp or (round(vm/vp, 2) if vm and vp else None)
    desagio = round((1 - vm/vp)*100, 1) if vm and vp else None

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("VM/cota",  f"R$ {vm:.2f}")
    c2.metric("VP/cota",  f"R$ {vp:.2f}" if vp else "—")
    c3.metric("Desagio",  f"{desagio:.1f}%" if desagio else "—", delta_color="inverse")
    c4.metric("DY 12m",   f"{dy:.1f}%" if dy else "—")
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    vm = vp = pvp = dy = desagio = None
    df_hist = None

st.divider()

# ── Grafico de cotacao ────────────────────────────────────────────────────────
if df_hist is not None:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_hist["data"], y=df_hist["preco"],
                             mode="lines", line=dict(color="#378ADD", width=2), name="VM"))
    if vp:
        fig.add_hline(y=vp, line_dash="dash", line_color="#E24B4A",
                      annotation_text=f"VP R${vp:.2f}")
    fig.update_layout(height=260, margin=dict(t=10,b=10,l=10,r=100),
                      yaxis_title="R$", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Painel de CRIs ────────────────────────────────────────────────────────────
st.sidebar.subheader("Dados do fundo")
vp_input = st.sidebar.number_input("VP/cota (R$) — atualizar mensalmente",
    min_value=0.0, value=st.session_state.get("vp_manual", 90.33), step=0.01, format="%.2f")
dy_input = st.sidebar.number_input("DY mensal (%) — ultimo pagamento",
    min_value=0.0, value=st.session_state.get("dy_manual", 1.22), step=0.01, format="%.2f")
if st.sidebar.button("Atualizar VP/DY"):
    st.session_state["vp_manual"] = vp_input
    st.session_state["dy_manual"] = dy_input
    st.rerun()
st.sidebar.caption(f"VP atual: R$ {vp_input:.2f} | DY: {dy_input:.2f}%")
st.sidebar.divider()
api_key = st.sidebar.text_input("Anthropic API Key (opcional)", type="password")
if st.sidebar.button("Limpar cache"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption("Yahoo Finance + Google/Bing News")

cri_sel = st.selectbox(
    "Selecionar CRI",
    [c["nome"] for c in CRIS],
    format_func=lambda x: f"{ICON[next(c['status'] for c in CRIS if c['nome']==x)]}  {x}  —  {next(c['devedor'] for c in CRIS if c['nome']==x)}"
)
cri = next(c for c in CRIS if c["nome"] == cri_sel)

# Card do CRI
cor = COR[cri["status"]]
cols = st.columns([3, 1, 1, 1, 1])
cols[0].markdown(f"**{ICON[cri['status']]} {cri['nome']}** &nbsp; `{cri['taxa']}` &nbsp; venc. {cri['venc']}<br><small>{cri['devedor']} · Sec: {cri['sec']} · {cri['pl']}% PL</small>", unsafe_allow_html=True)
cols[1].metric("HTM", f"R$ {cri['htmk']/1000:.1f}M")
cols[2].metric("Recovery base", f"{cri['r_base']}%")
cols[3].metric("Recovery R$", f"R$ {cri['htmk']*cri['r_base']/100/1000:.1f}M")
cols[4].metric("Perda est.", f"R$ {cri['htmk']*(1-cri['r_base']/100)/1000:.1f}M", delta_color="inverse")

if cri["alerta"]:
    st.warning(f"⚠️  {cri['alerta']}")

st.divider()

# Noticias do CRI selecionado
query = st.text_input("Query de busca", value=cri["queries"][0])
b1, b2, b3 = st.columns([1, 1, 5])
btn_buscar = b1.button("Buscar noticias", type="primary")
btn_ai     = b2.button("Sintetizar IA", disabled=not api_key)

if btn_buscar or btn_ai:
    with st.spinner("Buscando..."):
        noticias = buscar_noticias(query)
    if not noticias:
        st.warning("Sem resultados. Tente uma query mais simples.")
    else:
        if btn_ai and api_key:
            try:
                textos = "\n".join(f"- {n['t']}" for n in noticias)
                r = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                             "content-type": "application/json"},
                    json={"model": "claude-sonnet-4-20250514", "max_tokens": 250,
                          "messages": [{"role": "user", "content":
                              f"Analista de credito: sintetize em 3 frases as novidades sobre "
                              f"{cri['nome']} (devedor: {cri['devedor']}, sec: {cri['sec']}, "
                              f"status: {cri['status']}). O risco melhorou, piorou ou estavel?\n\n{textos}"}]},
                    timeout=20
                )
                st.info(r.json()["content"][0]["text"])
            except Exception as e:
                st.error(f"Erro IA: {e}")
        for n in noticias:
            st.markdown(f"- [{n['t']}]({n['l']}) `{n['d']}`")

st.divider()

# ── Tabela de todos os CRIs ───────────────────────────────────────────────────
st.subheader("Carteira completa")
df_t = pd.DataFrame([{
    "": ICON[c["status"]],
    "CRI": c["nome"],
    "Devedor": c["devedor"],
    "Sec": c["sec"],
    "% PL": c["pl"],
    "Taxa": c["taxa"],
    "Venc": c["venc"],
    "HTM Rk": c["htmk"],
    "Rec. Base": f"{c['r_base']}%",
    "Alerta": c["alerta"] or "—",
} for c in CRIS])
st.dataframe(df_t, use_container_width=True, hide_index=True)
st.caption("Carteira: BREI — Relatorio jan/2026")
