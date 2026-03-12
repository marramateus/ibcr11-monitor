# IBCR11 — Monitor de CRIs

Dashboard local para monitoramento dos CRIs da carteira do FII IBCR11.
Elaborado por Rio das Pedras Investimentos — uso interno.

---

## Funcionalidades

- **Carteira completa**: visualização de todos os 11 CRIs com status, recovery estimado e composição
- **Busca de notícias**: Google News por CRI com queries pré-configuradas (editáveis)
- **Síntese por IA**: integração com Claude API para sintetizar notícias automaticamente (opcional)
- **Cotação B3**: gráfico de preço e volume via Yahoo Finance (tempo real, ~15min delay)
- **Stress test**: cenários best/base/worst com valores ajustados por recovery e IRR esperado
- **Banco de dados local**: SQLite salva histórico de buscas

---

## Instalação

### 1. Pré-requisitos
- Python 3.9+

### 2. Instalar dependências

```bash
cd ibcr11_monitor
pip install -r requirements.txt
```

### 3. Rodar o dashboard

```bash
streamlit run app.py
```

Abre automaticamente em `http://localhost:8501`

---

## Configuração

No painel lateral do dashboard:

| Campo | Descrição |
|-------|-----------|
| **Anthropic API Key** | Opcional. Habilita síntese automática de notícias por IA. Obtenha em [console.anthropic.com](https://console.anthropic.com) |
| **Fontes ativas** | Liga/desliga cada fonte de dados individualmente |
| **Filtrar carteira** | Filtra ativos por status (Crítico / Atenção / Normal) |

---

## Fontes de dados

| Fonte | Dado | Frequência | Limitações |
|-------|------|------------|------------|
| Yahoo Finance | Cotação IBCR11.SA | Tempo real (~15min delay) | Gratuito, sem autenticação |
| Google News RSS | Notícias por CRI | Sob demanda | Pode retornar resultados irrelevantes |
| CVM dados abertos | Comunicados | Sob demanda | Requer parsing manual de PDFs |
| Anthropic Claude API | Síntese IA | Sob demanda | Requer API key paga |

### Fontes manuais recomendadas (checar mensalmente)
- **Comunicados IBCR11**: https://www.rad.cvm.gov.br → pesquisar IBCR11
- **Relatórios Virgo**: https://virgo.com.br/securitizadora/
- **Relatórios True**: https://www.truesec.com.br/

---

## Estrutura de arquivos

```
ibcr11_monitor/
├── app.py              # Dashboard principal
├── requirements.txt    # Dependências Python
├── README.md           # Este arquivo
└── ibcr11_data.db      # Banco de dados SQLite (criado automaticamente)
```

---

## Atualização dos dados base

Os dados de Jan/2026 estão hardcoded em `app.py` na lista `CRIS`. Para atualizar com um novo relatório mensal, edite os campos:
- `recovery_best`, `recovery_base`, `recovery_worst`
- `htmk` (valor HTM em R$ mil)
- `mtmk` (valor MTM em R$ mil)
- `status` (CRÍTICO / ATENÇÃO / NORMAL)
- `query` (query de busca de notícias)

---

## Notas

- **Confidencial** — material de uso interno. Não constitui oferta ou recomendação de investimento.
- Performance passada não é garantia de performance futura.
- As estimativas de recovery são modelagens analíticas, não laudos de avaliação.
