# Élpis — Buscador de Vagas com IA (Brasil & Internacional) — v24 (Viewport Lock Perfeito)
# © 2026 INOVHIA Desenvolvimento Tecnológico. Todos os direitos reservados.
# Contato: Jeferson Alexandre — +55 31 99484-8343
# É proibida a reprodução, total ou parcial, sem autorização prévia da INOVHIA.
# Instale dependências com: python -m pip install -r requirements.txt
# Execute com:              python -m streamlit run elpis_app_v23_1.py

from collections import Counter
import html
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import folium
import streamlit as st
from streamlit_folium import st_folium

import elpis_fontes as core
import elpis_boas_vindas as bv

APP_VERSION = "2026-10-02-v24.23-Selectbox-Harmonized"
st.set_page_config(page_title=f"Élpis {APP_VERSION}", layout="wide", initial_sidebar_state="collapsed")

# Previne tradução automática indevida do Chrome
st.html("""<script>
try { const d = window.parent.document;
  d.documentElement.setAttribute('lang', 'pt-BR'); d.documentElement.setAttribute('translate', 'no');
  d.documentElement.classList.add('notranslate');
  if (!d.querySelector('meta[name="google"]')) { const m = d.createElement('meta');
    m.name = 'google'; m.content = 'notranslate'; d.head.appendChild(m); } } catch (e) {}
</script>""", unsafe_allow_javascript=True)

# 1. Injeta CSS base
try:
    st.markdown(bv.CSS, unsafe_allow_html=True)
except Exception:
    pass

# 2. DESIGN SYSTEM CORPORATIVO ÉLPIS (Zero Outer Scroll & Tipografia Harmonizada)
st.markdown("""
<style>
:root {
  --primary-color: #142F50 !important;
  --elpis-primary: #142F50;
  --elpis-primary-dark: #0A192F;
  --elpis-orange: #F6A000;
  --elpis-orange-hover: #D98900;
  --status-success: #10B981;
  --status-success-bg: #D2F7EF;
  --status-info: #3B82F6;
  --status-info-bg: #E0E7FF;
  --status-warning: #F59E0B;
  --status-warning-bg: #FFF2C7;
  --status-neutral: #94A3B8;
  --status-neutral-bg: #F1F5F9;
  --background: #F4F8FD;
  --surface: #FFFFFF;
  --text-primary: #111827;
  --text-secondary: #64748B;
  --text-light: #FFFFFF;
  --border: #E2E8F0;
  --border-dark: #CBD5E1;
  --shadow-sm: 0 1px 4px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 16px rgba(15, 23, 42, 0.08);
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
}

/* Oculta cabeçalho nativo e barra lateral do Streamlit */
header[data-testid="stHeader"], [data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display: none !important;}

/* Oculta contentores invisíveis para cortar espaço branco no topo */
div[data-testid="stElementContainer"]:has(> style),
div[data-testid="stElementContainer"]:has(> script),
div[data-testid="stElementContainer"]:empty {
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Trava a tela para impedir rolagem global da janela */
html, body, [data-testid="stAppViewContainer"] {
    overflow-x: hidden !important;
    overflow-y: hidden !important;
}
.block-container {
    padding-top: 0.25rem !important;
    padding-bottom: 0.2rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100% !important;
}
.stApp {background: var(--background) !important;}

/* =========================================================
   BLINDAGEM TOTAL DOS CHECKBOXES (AZUL CORPORATIVO ÉLPIS)
   ========================================================= */
[data-testid="stCheckbox"] {
    margin: 0 !important;
    padding: 0 !important;
}
[data-testid="stCheckbox"] label {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    cursor: pointer !important;
}
[data-testid="stCheckbox"] label div[data-baseweb="checkbox"] {
    flex-shrink: 0 !important;
    width: 16px !important;
    height: 16px !important;
}
[data-testid="stCheckbox"] input:checked + div,
[data-testid="stCheckbox"] input:checked ~ div,
[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"],
[data-testid="stCheckbox"] div[aria-checked="true"],
[data-testid="stCheckbox"] span[aria-checked="true"],
div[data-baseweb="checkbox"]:has(input:checked) > div,
label[data-baseweb="checkbox"]:has(input:checked) div,
[data-testid="stCheckbox"] label div:has(> svg) {
    background-color: var(--elpis-primary) !important;
    border-color: var(--elpis-primary) !important;
}
[data-testid="stCheckbox"] svg {
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}

/* =========================================================
   PAINEL LATERAL ESQUERDO: PADRONIZAÇÃO TIPOGRÁFICA GERAL
   ========================================================= */
.f-title {
    font-size: 13px !important;
    font-weight: 700 !important;
    color: var(--elpis-primary) !important;
    padding-top: 2px !important;
}
.f-sec {
    font-size: 11.5px !important;
    font-weight: 700 !important;
    color: var(--elpis-primary) !important;
    margin: 6px 0 3px 0 !important;
    display: flex !important;
    align-items: center !important;
}
.f-sec .help {
    display: inline-block;
    width: 13px;
    height: 13px;
    line-height: 13px;
    text-align: center;
    border: 1px solid var(--border-dark);
    border-radius: 50%;
    font-size: 8px;
    color: var(--text-secondary);
    margin-left: 4px;
    cursor: help;
}

.st-key-painel_filtros [data-testid="stCheckbox"] label p {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
    line-height: 1.2 !important;
    margin: 0 !important;
    white-space: nowrap !important;
}

.st-key-lista_fontes [data-testid="stHorizontalBlock"] {
    margin-bottom: -8px !important;
    align-items: center !important;
    min-height: 24px !important;
}
.st-key-lista_fontes [data-testid="column"] {
    display: flex !important;
    align-items: center !important;
}

.sb {
    display: inline-block;
    border-radius: 6px;
    padding: 2px 6px !important;
    font-size: 9.5px !important;
    font-weight: 600 !important;
    white-space: nowrap;
    line-height: 1.2;
}
.sb-ok {background: var(--status-success-bg); color: #087F68;}
.sb-wait {background: var(--status-warning-bg); color: #9A5800;}
.sb-off {background: var(--status-neutral-bg); color: #475569;}

/* =========================================================
   SELETORES: ORDEM & PUBLICAÇÃO (BLINDADOS CONTRA VERMELHO)
   ========================================================= */
.st-key-painel_filtros [data-testid="stSelectbox"] {
    margin-bottom: 3px !important;
    margin-top: 1px !important;
}
.st-key-painel_filtros [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    min-height: 28px !important;
    height: 28px !important;
    padding: 0 6px !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    background-color: var(--surface) !important;
    box-shadow: none !important;
    outline: none !important;
}
/* Elimina a borda vermelha ao focar / clicar */
.st-key-painel_filtros [data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
.st-key-painel_filtros [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus,
.st-key-painel_filtros [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
.st-key-painel_filtros [data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div {
    border-color: var(--elpis-primary) !important;
    box-shadow: 0 0 0 1px var(--elpis-primary) !important;
    outline: none !important;
}
.st-key-painel_filtros [data-testid="stSelectbox"] div[data-baseweb="select"] span,
.st-key-painel_filtros [data-testid="stSelectbox"] div[data-baseweb="select"] div,
.st-key-painel_filtros [data-testid="stSelectbox"] div[data-baseweb="select"] input {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
    line-height: 26px !important;
}
.st-key-painel_filtros [data-testid="stSelectbox"] svg {
    width: 14px !important;
    height: 14px !important;
    color: var(--text-secondary) !important;
}

/* =========================================================
   POPUP DO MENU SUSPENSO (LISTA DE OPÇÕES COMPACTA & 11px)
   ========================================================= */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div {
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-md) !important;
    border: 1px solid var(--border) !important;
    background-color: var(--surface) !important;
}
div[data-baseweb="popover"] ul,
ul[role="listbox"] {
    padding: 3px !important;
    max-height: 160px !important;
}
div[data-baseweb="popover"] li,
div[data-baseweb="menu"] li,
ul[role="listbox"] li {
    font-size: 11px !important;
    padding: 4px 8px !important;
    min-height: 24px !important;
    height: 25px !important;
    line-height: 1.2 !important;
    border-radius: 4px !important;
}
div[data-baseweb="popover"] li *,
div[data-baseweb="menu"] li *,
ul[role="listbox"] li * {
    font-size: 11px !important;
    line-height: 1.2 !important;
}
div[data-baseweb="popover"] li[aria-selected="true"],
ul[role="listbox"] li[aria-selected="true"] {
    background-color: #E0E7FF !important;
    color: var(--elpis-primary) !important;
    font-weight: 600 !important;
}
div[data-baseweb="popover"] li:hover,
ul[role="listbox"] li:hover {
    background-color: #F1F5F9 !important;
}

/* 5. CAIXA INFORMATIVA E SESSÃO */
.info-box {
    display: flex;
    gap: 6px;
    align-items: center;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 6px 8px;
    margin: 6px 0;
    font-size: 10px;
    color: var(--text-secondary);
}
.info-box b {
    display: block;
    color: var(--elpis-primary);
    font-size: 10.5px;
}
.st-key-limpar button {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    color: var(--status-info) !important;
    font-size: 11px !important;
    min-height: 0 !important;
    padding: 0 !important;
    float: right;
}
.st-key-limpar button p {
    color: var(--status-info) !important;
    font-size: 11px !important;
}

/* =========================================================
   EXPANDER: IA & OPÇÕES (HARMONIZADO)
   ========================================================= */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--surface) !important;
    margin-top: 4px !important;
    margin-bottom: 2px !important;
}
[data-testid="stExpander"] details summary {
    padding: 4px 8px !important;
}
[data-testid="stExpander"] details summary p,
[data-testid="stExpander"] details summary span {
    font-size: 11px !important;
    font-weight: 700 !important;
    color: var(--elpis-primary) !important;
}
[data-testid="stExpander"] details div[data-testid="stExpanderDetails"] {
    padding: 6px 8px !important;
}
[data-testid="stExpander"] label p,
[data-testid="stExpander"] label span,
[data-testid="stExpander"] [data-testid="stWidgetLabel"] p {
    font-size: 10.5px !important;
    font-weight: 700 !important;
    color: var(--elpis-primary) !important;
    margin-bottom: 2px !important;
}
[data-testid="stExpander"] [data-testid="stSlider"] div[role="slider"] {
    background-color: var(--elpis-primary) !important;
    border: 2px solid #FFFFFF !important;
}
[data-testid="stExpander"] [data-testid="stSlider"] div[data-baseweb="slider"] div[style*="background-color"] {
    background-color: var(--elpis-primary) !important;
}
[data-testid="stExpander"] [data-testid="stSlider"] div[data-testid="stMarkdownContainer"] p {
    color: var(--elpis-primary) !important;
    font-weight: 700 !important;
    font-size: 10.5px !important;
}
[data-testid="stExpander"] input {
    min-height: 26px !important;
    height: 26px !important;
    font-size: 10.5px !important;
    padding: 2px 8px !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stExpander"] button {
    min-height: 24px !important;
    height: 24px !important;
    padding: 2px 6px !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stExpander"] button p {
    font-size: 10.5px !important;
}
[data-testid="stExpander"] [data-testid="stCheckbox"] {
    margin-top: 3px !important;
    margin-bottom: 2px !important;
}
[data-testid="stExpander"] [data-testid="stCheckbox"] label p {
    font-size: 10.5px !important;
    font-weight: 500 !important;
    white-space: normal !important;
}

/* ---------- HEADER / FORMULÁRIO COMPACTO ---------- */
[data-testid="stForm"] {
    background: var(--elpis-primary) !important; border: 0 !important;
    border-radius: var(--radius-md) !important; padding: 6px 14px !important;
    box-shadow: var(--shadow-md) !important; margin-top: 0.1rem !important; margin-bottom: 0.4rem !important;
}
[data-testid="stForm"] input, [data-testid="stForm"] div[data-baseweb="select"] > div {
    background: var(--surface) !important; color: var(--text-primary) !important;
    border: none !important; border-radius: var(--radius-sm) !important;
    min-height: 36px !important; height: 36px !important; font-size: 13px !important;
}
[data-testid="stForm"] button[kind="primary"], [data-testid="stForm"] button[kind="primaryFormSubmit"] {
    background: var(--elpis-orange) !important; color: var(--elpis-primary-dark) !important;
    border: 0 !important; border-radius: var(--radius-sm) !important;
    min-height: 36px !important; height: 36px !important; font-weight: 800 !important;
    font-size: 13px !important; transition: background .2s ease;
}
[data-testid="stForm"] button[kind="primary"] p, [data-testid="stForm"] button[kind="primaryFormSubmit"] p {
    color: var(--elpis-primary-dark) !important; font-size: 13px !important;
}
[data-testid="stForm"] button[kind="primary"]:hover, [data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
    background: var(--elpis-orange-hover) !important;
}
.elpis-brand {color: var(--elpis-orange); font-weight: 800; font-size: 24px; line-height: 36px;}

/* ---------- CARTÕES DE VAGAS ---------- */
.job-card {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important; padding: 12px 14px !important;
    margin-bottom: 8px !important; box-shadow: var(--shadow-sm) !important;
    transition: box-shadow .15s ease;
}
.job-card:hover {box-shadow: var(--shadow-md) !important;}
.job-top {display:flex; justify-content:space-between; align-items:flex-start; gap:6px;}
.job-title {font-size: 15px; font-weight: 800; color: var(--elpis-primary); line-height: 1.25;}
.job-company {font-size: 12px; color: var(--text-secondary); margin-top: 2px;}
.job-desc {font-size: 11px; color: var(--text-secondary); margin: 6px 0 0 0; line-height: 1.4;}
.job-bottom {display:flex; justify-content:space-between; align-items:center; margin-top: 8px; gap: 6px;}
.age {font-size: 10px !important; margin: 0 !important; padding: 3px 6px !important; border-radius: 4px; font-weight: 600;}
.pill-green {background: var(--status-success-bg) !important; color: #087F68 !important;}
.pill-yellow {background: var(--status-warning-bg) !important; color: #9A5800 !important;}
.pill-gray {background: var(--status-neutral-bg) !important; color: #475569 !important;}

.badge-source {background: var(--status-info-bg); color: var(--elpis-primary); border-radius: 5px; padding: 3px 8px; font-size: 10px; font-weight: 600;}
.badge-global {background: var(--status-success-bg); color: #087F68;}
.badge-also {font-size: 9px; color: var(--status-neutral); margin-left: 4px;}

.btn-apply {
    background: var(--elpis-orange) !important; color: var(--elpis-primary-dark) !important;
    border-radius: var(--radius-sm) !important; padding: 5px 0 !important; width: 130px; text-align: center;
    font-size: 11px !important; font-weight: 800 !important; text-decoration: none !important;
    display: inline-block; transition: background .2s ease;
}
.btn-apply:hover {background: var(--elpis-orange-hover) !important; color: var(--text-light) !important;}

/* ---------- MAPA ---------- */
.st-key-mapa_card {background: #E8F0FB; border-radius: var(--radius-md); padding: 10px;}
.map-head {font-size: 14px; font-weight: 800; color: var(--elpis-primary); margin-bottom: 4px;}
.legend {background: var(--surface); border-radius: var(--radius-sm); padding: 4px 8px; margin-top: 4px;
    display:flex; justify-content:space-around; flex-wrap:wrap; gap:4px; font-size: 10px; color: var(--text-secondary);}
.dot {display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:3px; vertical-align:middle;}
iframe[title="streamlit_folium.st_folium"] {border-radius: var(--radius-sm) !important;}

/* ---------- RODAPÉ SLIM ---------- */
.elpis-footer {
    background-color: var(--elpis-primary-dark); color: var(--border-dark);
    padding: 6px 16px; border-radius: var(--radius-sm); margin-top: 6px;
    display: flex; justify-content: space-between; align-items: center; font-size: 0.72rem;
}
.elpis-footer b {color: var(--text-light);}
.elpis-footer .brand {color: var(--elpis-orange); font-weight: 800; font-size: 16px; margin-right: 8px;}
.elpis-footer a {color: var(--elpis-orange); text-decoration: underline; font-weight: bold;}

@media (max-width: 900px) {
    html, body, [data-testid="stAppViewContainer"] { overflow-y: auto !important; }
    .elpis-footer {flex-direction: column; text-align: center; gap: 4px;}
    [data-testid="stForm"] {padding: 6px !important;}
    .btn-apply {width: 110px;}
}
</style>
""", unsafe_allow_html=True)

CREDITO_EMPRESA = "INOVHIA Desenvolvimento Tecnológico"
CREDITO_CONTATO = "Jeferson Alexandre"
CREDITO_TELEFONE = "+55 31 99484-8343"
CREDITO_TEL_LINK = "+5531994848343"


def rodape_inovhia():
    st.markdown(
        f"<div class='elpis-footer'>"
        f"<div><span class='brand'>Élpis</span>Conectando talentos a grandes oportunidades</div>"
        f"<div style='text-align:right'>Desenvolvido por <b>{html.escape(CREDITO_EMPRESA)}</b> | "
        f"{html.escape(CREDITO_CONTATO)} · <a href='tel:{CREDITO_TEL_LINK}'>{html.escape(CREDITO_TELEFONE)}</a></div>"
        f"</div>",
        unsafe_allow_html=True)


st.session_state.setdefault("vagas", [])
st.session_state.setdefault("resultados", [])

# ==========================================
# SESSÃO TEMPORÁRIA (SQLite local Seguro)
# ==========================================
FREE_DAILY_LIMIT = 10
SESSION_HOURS = 24
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpis_sessoes.sqlite3")
_HMAC_KEY = os.getenv("ELPIS_HASH_SALT", "elpis-troque-este-segredo")


def db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("""create table if not exists active_sessions (
        session_id text primary key, nome text not null, email_hash text,
        created_at text not null, expires_at text not null, searches integer not null default 0)""")
    con.execute("""create table if not exists access_metrics (
        id integer primary key autoincrement, event text not null, created_at text not null)""")
    con.commit()
    return con


def agora(): return datetime.now(timezone.utc)


def limpar_sessoes_expiradas(con):
    con.execute("delete from active_sessions where expires_at < ?", (agora().isoformat(),))
    con.commit()


def hash_email(email):
    email = (email or "").strip().lower()
    return sha256((_HMAC_KEY + email).encode("utf-8")).hexdigest() if email else None


def criar_sessao(nome, email):
    con = db(); limpar_sessoes_expiradas(con)
    sid, now = uuid.uuid4().hex, agora()
    con.execute("insert into active_sessions values (?, ?, ?, ?, ?, 0)",
                (sid, nome, hash_email(email), now.isoformat(), (now + timedelta(hours=SESSION_HOURS)).isoformat()))
    con.execute("insert into access_metrics(event, created_at) values (?, ?)", ("entrada", now.isoformat()))
    con.commit(); con.close()
    return sid


def sessao_atual(sid):
    if not sid: return None
    con = db(); limpar_sessoes_expiradas(con)
    row = con.execute("select * from active_sessions where session_id = ?", (sid,)).fetchone()
    con.close()
    return dict(row) if row else None


def apagar_sessao(sid):
    if not sid: return
    con = db()
    con.execute("delete from active_sessions where session_id = ?", (sid,))
    con.execute("insert into access_metrics(event, created_at) values (?, ?)", ("saida", agora().isoformat()))
    con.commit(); con.close()


def usage_today(sid):
    row = sessao_atual(sid)
    return int(row["searches"]) if row else 0


def record_usage(sid):
    con = db()
    con.execute("update active_sessions set searches = searches + 1 where session_id = ?", (sid,))
    con.commit(); con.close()


@st.dialog("Bem-vindo à Élpis")
def cadastro_dialog():
    st.markdown("Identifique-se para iniciar a sua sessão gratuita. **Sem senha e sem e-mail.**")
    nome = st.text_input("Nome completo ou profissional", placeholder="Como deseja ser identificado?", key="dlg_nome").strip()
    email = st.text_input("E-mail (opcional)", placeholder="Não será verificado nesta versão", key="dlg_email").strip()
    aceite = st.checkbox("Aceito os Termos de Uso e Política de Privacidade.", key="dlg_aceite")
    st.caption("A sessão expira em 24 horas.")
    if st.button("Acessar Plataforma", type="primary", use_container_width=True):
        if not nome or not aceite:
            st.warning("Informe o seu nome e aceite a Política.")
        else:
            st.session_state.temporary_session_id = criar_sessao(nome, email)
            st.session_state.busca_pendente = st.session_state.pop("busca_aguardando", None)
            st.rerun()


sid = st.session_state.get("temporary_session_id")
current_session = sessao_atual(sid)

# ==========================================
# FUNÇÕES DE FORMATAÇÃO E STATUS
# ==========================================
MODALIDADES = ("Presencial", "Remoto", "Híbrido")


def esc(t): return html.escape(str(t or ""), quote=True)


def classe_idade(dias):
    if dias is None or dias > 10: return "pill-gray"
    return "pill-green" if dias <= 2 else "pill-yellow"


def texto_idade(dias):
    if dias is None or dias > 365: return "sem data"
    return "hoje" if dias == 0 else ("há 1 dia" if dias == 1 else f"há {dias} dias")


def modalidade(v):
    t = f"{v.get('titulo', '')} {v.get('local', '')} {v.get('resumo', '')}".lower()
    if any(k in t for k in ("híbrido", "hibrido", "hybrid")): return "Híbrido"
    return "Remoto" if core.eh_remoto(v) else "Presencial"


def badge_fonte(nome, mapa, rodando):
    r = mapa.get(nome)
    if r is None:
        return '<span class="sb sb-wait">…</span>' if rodando else ""
    if r.status == "ok":
        cache = any("cache" in x for x in r.notas)
        t = "cache" if cache else f"{r.ms / 1000:.1f}s"
        return f'<span class="sb sb-ok">{len(r.itens)} · {t}</span>'
    if r.status == "vazio": return '<span class="sb sb-wait">0</span>'
    if r.status == "timeout": return '<span class="sb sb-off">timeout</span>'
    return '<span class="sb sb-off">erro</span>'


def analisar_com_gemini(vagas, cargo, nivel, chave):
    base = [{"i": i, "titulo": v["titulo"], "empresa": v["empresa"], "local": v["local"]} for i, v in enumerate(vagas)]
    prompt = (f"Busca: {cargo} ({nivel}). Para cada vaga REAL abaixo, escreva 1 frase curta sobre aderência ao perfil "
              "usando SOMENTE título/empresa/local fornecidos, sem inventar requisitos. Responda APENAS array JSON "
              f'puro: [{{"i":0,"analise":"..."}}]\n{json.dumps(base, ensure_ascii=False)}')
    modelo = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    try:
        from google import genai
        texto = genai.Client(api_key=chave).models.generate_content(
            model=modelo, contents=prompt, config={"response_mime_type": "application/json"}).text
    except ImportError:
        import google.generativeai as legado
        legado.configure(api_key=chave)
        texto = legado.GenerativeModel(modelo).generate_content(prompt).text
    for it in json.loads(texto.replace('```json', '').replace('```', '').strip()):
        idx = int(it["i"])
        if 0 <= idx < len(vagas): vagas[idx]["analise"] = it["analise"]


# ==========================================
# MOTOR GEOESPACIAL ROBUSTO (SEM CRASH NO LEAFLET)
# ==========================================
def montar_mapa(vagas, aproximar):
    m = folium.Map(location=[-15.7801, -47.9292], zoom_start=4, min_zoom=2, tiles="OpenStreetMap",
                   world_copy_jump=True, control_scale=False)
    from folium.plugins import MarkerCluster
    grupo = MarkerCluster(options={"maxClusterRadius": 35}).add_to(m)
    pts = []
    for v in vagas:
        lat, lon = v.get("lat"), v.get("lon")
        if lat is None or lon is None:
            continue
        try:
            lat, lon = float(lat), float(lon)
        except (ValueError, TypeError):
            continue

        pts.append([lat, lon])
        d = core.idade_dias(v.get("data"))
        cor = "#94A3B8" if d is None or d > 10 else ("#10B981" if d <= 2 else "#F59E0B")

        empresa_limpa = str(v.get('empresa', '')).replace('"', "'").replace('\n', ' ').strip()
        titulo_limpo = str(v.get('titulo', '')).replace('"', "'").replace('\n', ' ').strip()
        tt_texto = f"{empresa_limpa} | {titulo_limpo}"[:120]

        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color="white",
            weight=1.5,
            fill=True,
            fill_color=cor,
            fill_opacity=1,
            tooltip=tt_texto
        ).add_to(grupo)

    if pts and aproximar:
        unique_pts = set((p[0], p[1]) for p in pts)
        if len(unique_pts) == 1:
            m.location = pts[0]
            m.zoom_start = 6
        else:
            m.fit_bounds(pts, max_zoom=6, padding=(25, 25))
    return m


def limpar_filtros():
    for n in core.disponiveis(): st.session_state[f"fonte_{n}"] = True
    for m in MODALIDADES: st.session_state[f"mod_{m}"] = False
    rid_ = st.session_state.get("resultado_id", 0)
    for k in (f"f_per_{rid_}", f"f_ord_{rid_}"): st.session_state.pop(k, None)


# ==========================================
# 1) HEADER DE BUSCA ULTRA-COMPACTO
# ==========================================
with st.form("search_form"):
    c0, c1, c2, c3, c4 = st.columns([1.1, 3.8, 2.7, 1.8, 1.4], vertical_alignment="center")
    with c0: st.markdown("<div class='elpis-brand'>Élpis</div>", unsafe_allow_html=True)
    with c1: cargo = st.text_input("Cargo / Função", placeholder="💼  Cargo / Função", label_visibility="collapsed")
    with c2: local = st.text_input("Localidade", placeholder="📍  Localidade (ex: Belo Horizonte)", label_visibility="collapsed")
    with c3: nivel = st.selectbox("Senioridade", ["(qualquer)", "Analista", "Especialista", "Coordenador", "Gerente", "Diretor", "VP"], label_visibility="collapsed")
    with c4: buscar = st.form_submit_button("🔍  Buscar", type="primary", use_container_width=True)

# ==========================================
# 2) ESTRUTURA HORIZONTAL CALIBRADA (VIEWPORT)
# ==========================================
col_filtros, col_main = st.columns([1.38, 4.62], gap="small")
with col_main:
    status_slot = st.container()
    aviso_slot = st.container()
    col_lista, col_mapa = st.columns([1.45, 1.15], gap="small")

# ==========================================
# 3) PAINEL DE FILTROS ALINHADO (ALTURA TRAVADA A 510px)
# ==========================================
mapa_prev = {r.nome: r for r in st.session_state.get("resultados", [])}
todas = core.disponiveis()
fontes_ativas, badge_slots = [], {}

with col_filtros:
    with st.container(height=510, border=False, key="painel_filtros"):
        h1, h2 = st.columns(2, vertical_alignment="center")
        h1.markdown("<div class='f-title'>🎚️ Filtros</div>", unsafe_allow_html=True)
        h2.button("Limpar", key="limpar", on_click=limpar_filtros)

        st.markdown("<div class='f-sec'>🗂️ Fontes de vagas "
                    "<span class='help' title='Motores consultados'>?</span></div>",
                    unsafe_allow_html=True)
        with st.container(height=160, key="lista_fontes"):
            for nome in todas:
                st.session_state.setdefault(f"fonte_{nome}", True)
                ca, cb = st.columns([5, 4], vertical_alignment="center", gap="small")
                if ca.checkbox(nome, key=f"fonte_{nome}"): fontes_ativas.append(nome)
                badge_slots[nome] = cb.empty()
                badge_slots[nome].markdown(badge_fonte(nome, mapa_prev, False), unsafe_allow_html=True)

        st.markdown("<div class='f-sec'>🎛️ Modalidade</div>", unsafe_allow_html=True)
        with st.container(key="sec_modalidade"):
            c_pres, c_rem, c_hib = st.columns([1.35, 1.0, 1.0], gap="small")
            mod_cols = [c_pres, c_rem, c_hib]
            mods = [m for m, c in zip(MODALIDADES, mod_cols) if c.checkbox(m, key=f"mod_{m}")]

        filtros_pos = st.container()

        st.markdown(
            "<div class='info-box'><svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#142F50' "
            "stroke-width='1.8'><path d='M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z'/><path d='M9 12l2 2 4-4'/></svg>"
            "<div><b>Tempo Real</b>Filtros e IA ativos</div></div>",
            unsafe_allow_html=True)

        # Sessão
        if current_session:
            st.markdown(f"<div style='color:var(--elpis-primary);font-weight:700;font-size:11px;'>👤 {esc(current_session['nome'])}</div>",
                        unsafe_allow_html=True)
            uso_slot = st.empty()
            uso_slot.caption(f"Uso: **{usage_today(sid)} / {FREE_DAILY_LIMIT}** gratuitas")
            if st.button("Sair", use_container_width=True):
                apagar_sessao(sid)
                st.session_state.pop("temporary_session_id", None)
                st.session_state.vagas, st.session_state.resultados = [], []
                st.rerun()
        else:
            uso_slot = None
            st.caption("Visitante.")

        # Opções de IA e Configuração Harmonizadas
        with st.expander("⚙️ IA & Opções"):
            prazo = st.slider("Timeout (s)", 8, 40, 20)
            st.session_state.setdefault("gemini_key", os.getenv("GEMINI_API_KEY", ""))
            st.session_state.setdefault("gemini_connected", False)
            st.session_state.setdefault("gemini_status", "")
            chave_digitada = st.text_input("Chave Gemini", type="password", value=st.session_state["gemini_key"],
                                           placeholder="Chave opcional")
            col_con, col_des = st.columns(2)
            if col_con.button("Conectar", use_container_width=True):
                chave_t = (chave_digitada or "").strip()
                if not chave_t:
                    st.session_state["gemini_status"] = "Informe a chave."
                    st.session_state["gemini_connected"] = False
                else:
                    try:
                        from google import genai
                        cliente = genai.Client(api_key=chave_t)
                        if list(cliente.models.list()):
                            st.session_state["gemini_key"] = chave_t
                            st.session_state["gemini_connected"] = True
                            st.session_state["gemini_status"] = "Conectado."
                    except Exception:
                        st.session_state["gemini_connected"] = False
                        st.session_state["gemini_status"] = "Falha."
            if col_des.button("Remover", use_container_width=True):
                st.session_state["gemini_key"], st.session_state["gemini_connected"] = "", False
                st.session_state["gemini_status"] = "Desconectado."
            if st.session_state["gemini_connected"]: st.success(st.session_state["gemini_status"])
            elif st.session_state["gemini_status"]: st.caption(st.session_state["gemini_status"])
            chave = st.session_state["gemini_key"] if st.session_state["gemini_connected"] else ""
            aproximar = st.checkbox("Aproximar mapa", value=True)
            parciais = st.checkbox("Correspondências parciais", value=False)

# ==========================================
# 4) MOTOR DE EXECUÇÃO
# ==========================================
def executar_busca(params):
    termo, loc, niv = params["cargo"], params["local"], params["nivel"]
    st.markdown(bv.ESCONDER, unsafe_allow_html=True)
    brutas, resultados, t0 = [], [], time.perf_counter()

    for n in fontes_ativas:
        badge_slots[n].markdown(badge_fonte(n, {}, True), unsafe_allow_html=True)

    with status_slot:
        with st.status("Consultando bases de dados...", expanded=False) as box:
            for r in core.executar(fontes_ativas, termo, loc, prazo=prazo):
                resultados.append(r)
                brutas += r.itens
                if r.nome in badge_slots:
                    badge_slots[r.nome].markdown(badge_fonte(r.nome, {r.nome: r}, True), unsafe_allow_html=True)
                box.update(label=f"Processando {len(resultados)}/{len(fontes_ativas)} fontes · {len(brutas)} registos")
            box.update(label=f"Concluído em {time.perf_counter() - t0:.1f}s", state="complete", expanded=False)

    falhas = [r for r in resultados if r.status in ("erro", "timeout")]
    st.session_state.rede = core.verificar_rede() if len(falhas) >= max(3, len(resultados) // 2) else None
    unicas = core.consolidar(brutas, niv, limite=60, min_exatas=999 if parciais else 5)

    if aproximar and unicas:
        cache_loc, inicio, consultas = {}, time.perf_counter(), 0
        for v in unicas:
            lc = v["local"]
            if lc not in cache_loc:
                pos = core.geo_offline(lc)
                if not pos and not core.local_generico(lc) and consultas < 5 and time.perf_counter() - inicio < 6:
                    consultas += 1
                    pos = core.geo_nominatim(lc)
                cache_loc[lc] = pos
            v["lat"], v["lon"] = cache_loc[lc] or (None, None)
    else:
        for v in unicas: v["lat"], v["lon"] = None, None

    for v in unicas: v["analise"] = None

    record_usage(sid)
    if uso_slot is not None:
        uso_slot.caption(f"Uso: **{usage_today(sid)} / {FREE_DAILY_LIMIT}** gratuitas")

    st.session_state.update(vagas=unicas, resultados=resultados, tempo=time.perf_counter() - t0,
                            resultado_id=time.time_ns(), mostrar_n=15, termo_busca=termo,
                            nivel_busca=niv, local_busca=loc)


params = None
if buscar and not cargo.strip():
    st.warning("Informe o Cargo / Função para buscar.")
elif buscar:
    pedido = {"cargo": cargo.strip(), "local": local, "nivel": nivel}
    if current_session is None:
        st.session_state.busca_aguardando = pedido
        cadastro_dialog()
    else:
        params = pedido

if params is None and current_session is not None:
    params = st.session_state.pop("busca_pendente", None)

if params:
    if usage_today(sid) >= FREE_DAILY_LIMIT:
        aviso_slot.error("Limite gratuito diário atingido.")
    elif not fontes_ativas:
        aviso_slot.warning("Selecione ao menos uma fonte no painel de filtros.")
    else:
        executar_busca(params)

vagas_todas = st.session_state["vagas"]
resultados = st.session_state.get("resultados", [])
rid = st.session_state.get("resultado_id", 0)


def banner_falhas(resultados):
    falhas = [r for r in resultados if r.status in ("erro", "timeout")]
    if len(falhas) < max(3, len(resultados) // 2): return
    comuns = Counter((r.erro or "")[:90] for r in falhas).most_common(3)
    st.error(f"{len(falhas)} fontes falharam: " + " · ".join(f"**{n}×** `{msg}`" for msg, n in comuns))


with aviso_slot:
    banner_falhas(resultados)

# ==========================================
# 5) FILTROS DE RESULTADO (Data e Ordem Compactos & Sem Borda Vermelha)
# ==========================================
filtradas = vagas_todas
periodo = "Qualquer data"
ordem = "Relevância"

with filtros_pos:
    if vagas_todas:
        st.markdown("<div class='f-sec'>🗓️ Ordem & Publicação</div>", unsafe_allow_html=True)
        ordem = st.selectbox("Classificação", ["Relevância", "Mais recentes"], key=f"f_ord_{rid}", label_visibility="collapsed")
        periodo = st.selectbox("Período", ["Qualquer data", "Últimos 3 dias", "Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias"], key=f"f_per_{rid}", label_visibility="collapsed")

        dias_max = {"Últimos 3 dias": 3, "Últimos 7 dias": 7, "Últimos 15 dias": 15, "Últimos 30 dias": 30}.get(periodo)
        
        filtradas = [v for v in vagas_todas
                     if v["origem"] in fontes_ativas and (not mods or modalidade(v) in mods)
                     and (dias_max is None or (core.idade_dias(v.get("data")) is not None and core.idade_dias(v["data"]) <= dias_max))]
        if ordem == "Mais recentes":
            filtradas = sorted(filtradas, key=lambda v: v.get("data") or core.MIN_DATA, reverse=True)

        if chave and filtradas and st.button("✨ Insights IA", use_container_width=True):
            try:
                with st.spinner("Analisando..."):
                    analisar_com_gemini(filtradas[:12], st.session_state.get("termo_busca", ""),
                                        st.session_state.get("nivel_busca", "(qualquer)"), chave)
            except Exception as e:
                st.caption(f"Erro IA: {str(e)[:80]}")

# ==========================================
# 6) LISTA DE VAGAS (CENTRO - 510px COM BOTÃO INTERNO)
# ==========================================
with col_lista:
    if vagas_todas:
        st.caption(f"**{len(filtradas)}** vagas encontradas · busca em {st.session_state.get('tempo', 0):.1f}s")
    
    painel = st.container(height=510)
    with painel:
        if not vagas_todas and not resultados:
            st.markdown(bv.html_boas_vindas(len(fontes_ativas), FREE_DAILY_LIMIT), unsafe_allow_html=True)
        elif not vagas_todas:
            st.info("Utilize a barra superior para realizar uma pesquisa.")
        elif not filtradas:
            st.info("Nenhuma vaga atende aos filtros atuais.")

        n_mostrar = st.session_state.get("mostrar_n", 15)
        for v in filtradas[:n_mostrar]:
            dias = core.idade_dias(v.get("data"))
            descricao = (v.get("analise") or v.get("resumo") or "")[:200]
            link = v["link"] if core.eh_http(v.get("link")) else "#"
            badge_cls = "badge-source badge-global" if v.get("grupo") in ("Global", "Empresas") else "badge-source"
            origem_txt = f'{v["origem"]} · {v["grupo"]}' if v.get("grupo") else v["origem"]
            tambem = f'<span class="badge-also">também em {esc(", ".join(v["tambem"]))}</span>' if v.get("tambem") else ""
            desc_html = f'<div class="job-desc">{esc(descricao)}{"…" if len(descricao) >= 200 else ""}</div>' if descricao else ""

            st.markdown(
                f'<div class="job-card">'
                f'<div class="job-top"><div style="flex:1;"><div class="job-title">{esc(v["titulo"])}</div>'
                f'<div class="job-company">{esc(v["empresa"])} &middot; {esc(v["local"])}</div></div>'
                f'<div class="{classe_idade(dias)} age">🕒 {texto_idade(dias)}</div></div>'
                f'{desc_html}'
                f'<div class="job-bottom"><div><span class="{badge_cls}">{esc(origem_txt)}</span>{tambem}</div>'
                f'<a href="{esc(link)}" target="_blank" rel="noopener noreferrer" class="btn-apply">Candidatar-se</a>'
                f'</div></div>', unsafe_allow_html=True)

        if len(filtradas) > n_mostrar:
            if st.button(f"Carregar mais ({len(filtradas) - n_mostrar} restantes)", use_container_width=True):
                st.session_state.mostrar_n = n_mostrar + 15
                st.rerun()

# ==========================================
# 7) MAPA GEOESPACIAL REATIVO (DIREITA - 450px)
# ==========================================
with col_mapa:
    with st.container(key="mapa_card"):
        com_pino = sum(1 for v in filtradas if v.get("lat"))
        st.markdown(f"<div class='map-head'>📍 Mapa · {com_pino} vagas</div>", unsafe_allow_html=True)

        mapa_obj = montar_mapa(filtradas, aproximar)

        map_key = f"mapa_{rid}_{len(filtradas)}_{periodo}_{ordem}_{com_pino}"
        st_folium(mapa_obj, height=440, use_container_width=True, returned_objects=[], key=map_key)

        st.markdown(
            "<div class='legend'>"
            "<span><i class='dot' style='background:#10B981'></i>recente</span>"
            "<span><i class='dot' style='background:#F59E0B'></i>médio</span>"
            "<span><i class='dot' style='background:#94A3B8'></i>antigo</span></div>",
            unsafe_allow_html=True)

rodape_inovhia()
