# Élpis — Buscador de Vagas com IA (Brasil & Internacional) — v24 (layout painel)
# © 2026 INOVHIA Desenvolvimento Tecnológico. Todos os direitos reservados.
# Contato: Jeferson Alexandre — +55 31 99484-8343
# É proibida a reprodução, total ou parcial, sem autorização prévia da INOVHIA.
# Instale dependências com: python -m pip install -r requirements.txt
# Execute com:              python -m streamlit run elpis_app_v24_layout.py

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

APP_VERSION = "2026-10-02-v24.11-Painel"
st.set_page_config(page_title=f"Élpis {APP_VERSION}", layout="wide", initial_sidebar_state="collapsed")

# O Chrome oferece/aplica tradução automática e isso corrompe a interface
st.html("""<script>
try { const d = window.parent.document;
  d.documentElement.setAttribute('lang', 'pt-BR'); d.documentElement.setAttribute('translate', 'no');
  d.documentElement.classList.add('notranslate');
  if (!d.querySelector('meta[name="google"]')) { const m = d.createElement('meta');
    m.name = 'google'; m.content = 'notranslate'; d.head.appendChild(m); } } catch (e) {}
</script>""", unsafe_allow_javascript=True)

# 1. CSS padrão da tela de boas-vindas
try:
    st.markdown(bv.CSS, unsafe_allow_html=True)
except Exception:
    pass

# 2. DESIGN SYSTEM ÉLPIS (layout em painel: header · filtros · lista · mapa)
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
  --shadow-sm: 0 2px 6px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 8px 24px rgba(15, 23, 42, 0.08);
  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 20px;
}

header[data-testid="stHeader"], [data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display: none !important;}
.block-container {padding: 1rem 1.5rem 0 1.5rem !important; max-width: 100% !important;}
.stApp {background: var(--background) !important;}
div[data-baseweb="select"] ul {max-height: 220px !important;}

/* ---------- TAGS DO MULTISELECT ---------- */
div[data-baseweb="tag"], .stMultiSelect [data-baseweb="tag"] {
    background-color: var(--elpis-primary) !important; border-radius: 6px !important;
    padding: 2px 8px !important; margin: 2px !important; min-height: 24px !important;
}
div[data-baseweb="tag"] span, .stMultiSelect [data-baseweb="tag"] span {
    color: var(--text-light) !important; font-size: 11px !important; font-weight: 700 !important;
}
div[data-baseweb="tag"] svg {color: var(--text-light) !important; height: 12px !important; width: 12px !important;}

/* ---------- HEADER / FORM DE BUSCA ---------- */
[data-testid="stForm"] {
    background: var(--elpis-primary) !important; border: 0 !important;
    border-radius: var(--radius-md) !important; padding: 14px 22px !important;
    box-shadow: var(--shadow-md) !important; margin-bottom: 1rem !important;
}
[data-testid="stForm"] input, [data-testid="stForm"] div[data-baseweb="select"] > div {
    background: var(--surface) !important; color: var(--text-primary) !important;
    border: none !important; border-radius: var(--radius-sm) !important; min-height: 48px !important;
}
[data-testid="stForm"] button[kind="primary"], [data-testid="stForm"] button[kind="primaryFormSubmit"] {
    background: var(--elpis-orange) !important; color: var(--elpis-primary-dark) !important;
    border: 0 !important; border-radius: var(--radius-sm) !important;
    min-height: 48px !important; font-weight: 800 !important; transition: background .2s ease;
}
[data-testid="stForm"] button[kind="primary"] p, [data-testid="stForm"] button[kind="primaryFormSubmit"] p {
    color: var(--elpis-primary-dark) !important; font-size: 16px !important;
}
[data-testid="stForm"] button[kind="primary"]:hover, [data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
    background: var(--elpis-orange-hover) !important;
}
.elpis-brand {color: var(--elpis-orange); font-weight: 800; font-size: 34px; line-height: 48px;}

/* ---------- PAINEL DE FILTROS (ESQUERDA) ---------- */
.f-title {font-weight: 700; font-size: 15px; color: var(--elpis-primary); padding-top: 6px;}
.f-sec {font-weight: 700; font-size: 13px; color: var(--elpis-primary); margin: 16px 0 6px 0;}
.f-sec .help {display:inline-block; width:16px; height:16px; line-height:16px; text-align:center; border:1px solid var(--border-dark);
    border-radius:50%; font-size:10px; color:var(--text-secondary); margin-left:6px; cursor:help;}
.f-field {background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm);
    padding: 10px 12px; font-size: 13px; color: var(--text-primary);}
.f-field.empty {color: var(--text-secondary);}
.sb {display:inline-block; border-radius: 12px; padding: 3px 9px; font-size: 11px; font-weight: 600; white-space: nowrap;}
.sb-ok {background: var(--status-success-bg); color: #087F68;}
.sb-wait {background: var(--status-warning-bg); color: #9A5800;}
.sb-off {background: var(--status-neutral-bg); color: #475569;}
.info-box {display:flex; gap:12px; align-items:center; background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-md); padding: 14px; margin: 16px 0; font-size: 12px; color: var(--text-secondary);}
.info-box b {display:block; color: var(--elpis-primary); font-size: 13px;}
.st-key-painel_filtros [data-testid="stCheckbox"] p {font-size: 13px !important; color: var(--text-primary) !important;}
.st-key-limpar button {background: transparent !important; border: 0 !important; box-shadow: none !important;
    color: var(--status-info) !important; font-size: 12px !important; min-height: 0 !important; padding: 0 !important; float: right;}
.st-key-limpar button p {color: var(--status-info) !important; font-size: 12px !important;}

/* ---------- CHIPS DE FONTES (TOPO) ---------- */
.pill-green, .pill-yellow, .pill-gray {
    border-radius: var(--radius-lg) !important; padding: 8px 16px !important; font-size: 13px !important;
    display: inline-block; margin: 0 8px 8px 0; white-space: nowrap; font-weight: 500;
}
.pill-green {background: var(--status-success-bg) !important; color: #087F68 !important;}
.pill-yellow {background: var(--status-warning-bg) !important; color: #9A5800 !important;}
.pill-gray {background: var(--status-neutral-bg) !important; color: #475569 !important;}
.pill-green b, .pill-yellow b, .pill-gray b {font-weight: 700;}

/* ---------- CARTÕES DE VAGAS ---------- */
.job-card {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important; padding: 18px 20px !important;
    margin-bottom: 14px !important; box-shadow: var(--shadow-sm) !important;
    transition: box-shadow .15s ease;
}
.job-card:hover {box-shadow: var(--shadow-md) !important;}
.job-top {display:flex; justify-content:space-between; align-items:flex-start; gap:10px;}
.job-title {font-size: 18px; font-weight: 800; color: var(--elpis-primary); line-height: 1.3;}
.job-company {font-size: 14px; color: var(--text-secondary); margin-top: 2px;}
.job-desc {font-size: 13px; color: var(--text-secondary); margin: 10px 0 0 0; line-height: 1.5;}
.job-bottom {display:flex; justify-content:space-between; align-items:center; margin-top: 12px; gap: 10px;}
.age {font-size: 12px !important; margin: 0 !important; padding: 6px 12px !important;}
.badge-source {background: var(--status-info-bg); color: var(--elpis-primary); border-radius: 10px; padding: 6px 12px; font-size: 13px; font-weight: 600;}
.badge-global {background: var(--status-success-bg); color: #087F68;}
.badge-also {font-size: 11px; color: var(--status-neutral); margin-left: 8px;}
.btn-apply {
    background: var(--elpis-orange) !important; color: var(--elpis-primary-dark) !important;
    border-radius: var(--radius-sm) !important; padding: 10px 0 !important; width: 190px; text-align: center;
    font-size: 14px !important; font-weight: 800 !important; text-decoration: none !important;
    display: inline-block; transition: background .2s ease;
}
.btn-apply:hover {background: var(--elpis-orange-hover) !important; color: var(--text-light) !important;}

/* ---------- MAPA ---------- */
.st-key-mapa_card {background: #E8F0FB; border-radius: var(--radius-md); padding: 16px;}
.map-head {font-size: 17px; font-weight: 800; color: var(--elpis-primary); margin-bottom: 10px;}
.legend {background: var(--surface); border-radius: var(--radius-md); padding: 10px 16px; margin-top: 10px;
    display:flex; justify-content:space-around; flex-wrap:wrap; gap:8px; font-size: 12px; color: var(--text-secondary);}
.dot {display:inline-block; width:12px; height:12px; border-radius:50%; margin-right:6px; vertical-align:middle;}
iframe[title="streamlit_folium.st_folium"] {border-radius: var(--radius-sm) !important;}

/* ---------- RODAPÉ ---------- */
.elpis-footer {
    background-color: var(--elpis-primary-dark); color: var(--border-dark);
    padding: 14px 24px; border-radius: var(--radius-sm); margin-top: 24px;
    display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem;
}
.elpis-footer b {color: var(--text-light);}
.elpis-footer .brand {color: var(--elpis-orange); font-weight: 800; font-size: 22px; margin-right: 14px;}
.elpis-footer a {color: var(--elpis-orange); text-decoration: underline; font-weight: bold;}

@media (max-width: 900px) {
    .elpis-footer {flex-direction: column; text-align: center; gap: 10px;}
    [data-testid="stForm"] {padding: 12px !important;}
    .btn-apply {width: 140px;}
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
        f"<div style='text-align:right'>Desenvolvido por <b>{html.escape(CREDITO_EMPRESA)}</b><br>"
        f"{html.escape(CREDITO_CONTATO)} · Contato: <a href='tel:{CREDITO_TEL_LINK}'>{html.escape(CREDITO_TELEFONE)}</a></div>"
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
# FUNÇÕES DE FORMATAÇÃO, FILTRO E IA
# ==========================================
MODALIDADES = ("Presencial", "Remoto", "Híbrido")


def esc(t): return html.escape(str(t or ""), quote=True)


def classe_idade(dias):
    if dias is None or dias > 10: return "pill-gray"
    return "pill-green" if dias <= 2 else "pill-yellow"


def texto_idade(dias):
    if dias is None or dias > 365: return "data não informada"
    return "hoje" if dias == 0 else ("há 1 dia" if dias == 1 else f"há {dias} dias")


def modalidade(v):
    """Classifica a vaga em Híbrido / Remoto / Presencial a partir do texto disponível."""
    t = f"{v.get('titulo', '')} {v.get('local', '')} {v.get('resumo', '')}".lower()
    if any(k in t for k in ("híbrido", "hibrido", "hybrid")): return "Híbrido"
    return "Remoto" if core.eh_remoto(v) else "Presencial"


def chips_html(resultados, pendentes=()):
    partes = []
    for r in resultados:
        n, s = len(r.itens), f"{r.ms / 1000:.1f}".replace(".", ",")
        nome = f"<b>{esc(r.nome)}</b>"
        if r.status == "ok":
            cache = any("cache" in x for x in r.notas)
            classe, txt = "pill-green", f"{nome} · {n} · " + ("cache" if cache else f"{s} s")
        elif r.status == "vazio":
            classe, txt = "pill-yellow", f"{nome} · 0 vagas"
        elif r.status == "timeout":
            classe, txt = "pill-gray", f"{nome} · tempo esgotado"
        else:
            classe, txt = "pill-gray", f"{nome} · erro"
        dica = esc((r.erro + " | " if r.erro else "") + " | ".join(r.notas))
        partes.append(f'<span class="{classe}" title="{dica}">{txt}</span>')
    for nome in pendentes:
        partes.append(f'<span class="pill-yellow"><b>{esc(nome)}</b> · carregando…</span>')
    return f'<div style="margin:2px 0 10px 0;">{"".join(partes)}</div>'


def badge_fonte(nome, mapa, rodando):
    """Selo de status exibido ao lado de cada fonte no painel de filtros."""
    r = mapa.get(nome)
    if r is None:
        return '<span class="sb sb-wait">carregando…</span>' if rodando else ""
    if r.status == "ok":
        cache = any("cache" in x for x in r.notas)
        t = "cache" if cache else f"{r.ms / 1000:.1f}".replace(".", ",") + " s"
        return f'<span class="sb sb-ok">{len(r.itens)} · {t}</span>'
    if r.status == "vazio": return '<span class="sb sb-wait">0 vagas</span>'
    if r.status == "timeout": return '<span class="sb sb-off">tempo esgotado</span>'
    return '<span class="sb sb-off">erro</span>'


def campo(icone, rotulo, valor, vazio):
    cls = "f-field" if valor else "f-field empty"
    return f"<div class='f-sec'>{icone} {rotulo}</div><div class='{cls}'>{esc(valor) if valor else vazio}</div>"


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


def montar_mapa(vagas, aproximar):
    m = folium.Map(location=[-15.7801, -47.9292], zoom_start=4, min_zoom=2, tiles="CartoDB positron",
                   world_copy_jump=True, control_scale=False)
    from folium.plugins import MarkerCluster
    grupo = MarkerCluster(options={"maxClusterRadius": 35}).add_to(m)
    pts = []
    for v in vagas:
        if not v.get("lat"): continue
        pts.append([v["lat"], v["lon"]])
        d = core.idade_dias(v.get("data"))
        cor = "#94A3B8" if d is None or d > 10 else ("#10B981" if d <= 2 else "#F59E0B")
        folium.CircleMarker(location=[v["lat"], v["lon"]], radius=7, color="white", weight=1.5, fill=True,
                            fill_color=cor, fill_opacity=1, tooltip=f"{v['empresa']} | {v['titulo']}"[:120]).add_to(grupo)
    if pts and aproximar: m.fit_bounds(pts, max_zoom=6, padding=(40, 40))
    return m


def limpar_filtros():
    """Botão 'Limpar tudo': reativa todas as fontes e zera os filtros de resultado."""
    for n in core.disponiveis(): st.session_state[f"fonte_{n}"] = True
    for m in MODALIDADES: st.session_state[f"mod_{m}"] = False
    rid_ = st.session_state.get("resultado_id", 0)
    for k in (f"f_per_{rid_}", f"f_ord_{rid_}", f"f_ori_{rid_}"): st.session_state.pop(k, None)


# ==========================================
# 1) HEADER DE BUSCA (faixa azul superior)
# ==========================================
with st.form("search_form"):
    c0, c1, c2, c3, c4 = st.columns([1.2, 3.6, 2.6, 1.9, 1.6], vertical_alignment="center")
    with c0: st.markdown("<div class='elpis-brand'>Élpis</div>", unsafe_allow_html=True)
    with c1: cargo = st.text_input("Cargo / Função", placeholder="💼  Cargo / Função", label_visibility="collapsed")
    with c2: local = st.text_input("Localidade", placeholder="📍  Localidade (ex: Belo Horizonte)", label_visibility="collapsed")
    with c3: nivel = st.selectbox("Senioridade", ["(qualquer)", "Analista", "Especialista", "Coordenador", "Gerente", "Diretor", "VP"], label_visibility="collapsed")
    with c4: buscar = st.form_submit_button("🔍  Buscar", type="primary", use_container_width=True)

# ==========================================
# 2) ESQUELETO: [filtros] | [chips + (lista | mapa)]
# ==========================================
col_filtros, col_main = st.columns([1.35, 6.2], gap="medium")
with col_main:
    chips_slot = st.empty()
    status_slot = st.container()
    aviso_slot = st.container()
    col_lista, col_mapa = st.columns([3, 2], gap="medium")

# ==========================================
# 3) PAINEL DE FILTROS (coluna esquerda)
# ==========================================
mapa_prev = {r.nome: r for r in st.session_state.get("resultados", [])}
todas = core.disponiveis()
fontes_ativas, badge_slots = [], {}

with col_filtros:
    with st.container(key="painel_filtros"):
        h1, h2 = st.columns(2, vertical_alignment="center")
        h1.markdown("<div class='f-title'>🎚️ Filtros</div>", unsafe_allow_html=True)
        h2.button("Limpar tudo", key="limpar", on_click=limpar_filtros)

        st.markdown("<div class='f-sec'>🗂️ Fontes de vagas "
                    "<span class='help' title='Plataformas consultadas na próxima busca'>?</span></div>",
                    unsafe_allow_html=True)
        for nome in todas:
            st.session_state.setdefault(f"fonte_{nome}", True)
            ca, cb = st.columns([5, 4], vertical_alignment="center", gap="small")
            if ca.checkbox(nome, key=f"fonte_{nome}"): fontes_ativas.append(nome)
            badge_slots[nome] = cb.empty()
            badge_slots[nome].markdown(badge_fonte(nome, mapa_prev, False), unsafe_allow_html=True)

        # Resumo da busca atual (os campos de entrada ficam no header)
        st.markdown(
            campo("📍", "Localização", st.session_state.get("local_busca", ""), "Qualquer localidade")
            + campo("💼", "Cargo", st.session_state.get("termo_busca", ""), "Informe no topo")
            + campo("👤", "Senioridade", st.session_state.get("nivel_busca", ""), "(qualquer)"),
            unsafe_allow_html=True)

        st.markdown("<div class='f-sec'>🎛️ Modalidade</div>", unsafe_allow_html=True)
        mod_cols = st.columns(3, gap="small")
        mods = [m for m, c in zip(MODALIDADES, mod_cols) if c.checkbox(m, key=f"mod_{m}")]

        filtros_pos = st.container()  # preenchido após a busca (data, ordem, fonte, IA)

        st.markdown(
            "<div class='info-box'><svg width='30' height='30' viewBox='0 0 24 24' fill='none' stroke='#142F50' "
            "stroke-width='1.8'><path d='M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z'/><path d='M9 12l2 2 4-4'/></svg>"
            "<div><b>Vagas atualizadas em tempo real</b>Com filtros inteligentes e IA opcional</div></div>",
            unsafe_allow_html=True)

        # ---- Sessão ----
        if current_session:
            st.markdown(f"<div style='color:var(--elpis-primary);font-weight:700;font-size:14px;'>👤 {esc(current_session['nome'])}</div>",
                        unsafe_allow_html=True)
            uso_slot = st.empty()
            uso_slot.caption(f"Uso: **{usage_today(sid)} / {FREE_DAILY_LIMIT}** buscas gratuitas")
            if st.button("Encerrar sessão", use_container_width=True):
                apagar_sessao(sid)
                st.session_state.pop("temporary_session_id", None)
                st.session_state.vagas, st.session_state.resultados = [], []
                st.rerun()
        else:
            uso_slot = None
            st.caption("Acesso visitante.")

        # ---- Configurações (antiga barra lateral) ----
        with st.expander("⚙️ Configurações"):
            prazo = st.slider("Timeout da busca (segundos)", 8, 40, 20)
            st.markdown("**🧠 Inteligência Artificial**")
            st.session_state.setdefault("gemini_key", os.getenv("GEMINI_API_KEY", ""))
            st.session_state.setdefault("gemini_connected", False)
            st.session_state.setdefault("gemini_status", "")
            chave_digitada = st.text_input("Chave Gemini API", type="password", value=st.session_state["gemini_key"],
                                           placeholder="Insira a chave (opcional)")
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
                        st.session_state["gemini_status"] = "Falha na conexão."
            if col_des.button("Remover", use_container_width=True):
                st.session_state["gemini_key"], st.session_state["gemini_connected"] = "", False
                st.session_state["gemini_status"] = "Desconectado."
            if st.session_state["gemini_connected"]: st.success(st.session_state["gemini_status"])
            elif st.session_state["gemini_status"]: st.warning(st.session_state["gemini_status"])
            chave = st.session_state["gemini_key"] if st.session_state["gemini_connected"] else ""
            st.markdown("---")
            aproximar = st.checkbox("Aproximar mapa automaticamente", value=True)
            parciais = st.checkbox("Exibir correspondências parciais", value=False)

# ==========================================
# 4) MOTOR DE EXECUÇÃO
# ==========================================
def executar_busca(params):
    termo, loc, niv = params["cargo"], params["local"], params["nivel"]
    st.markdown(bv.ESCONDER, unsafe_allow_html=True)
    brutas, resultados, t0 = [], [], time.perf_counter()

    for n in fontes_ativas:
        badge_slots[n].markdown(badge_fonte(n, {}, True), unsafe_allow_html=True)
    chips_slot.markdown(chips_html([], fontes_ativas), unsafe_allow_html=True)

    with status_slot:
        with st.status("Consultando bases de dados...", expanded=False) as box:
            for r in core.executar(fontes_ativas, termo, loc, prazo=prazo):
                resultados.append(r)
                brutas += r.itens
                feitas = {x.nome for x in resultados}
                chips_slot.markdown(chips_html(resultados, [n for n in fontes_ativas if n not in feitas]),
                                    unsafe_allow_html=True)
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
        uso_slot.caption(f"Uso: **{usage_today(sid)} / {FREE_DAILY_LIMIT}** buscas gratuitas")

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

if resultados: chips_slot.markdown(chips_html(resultados), unsafe_allow_html=True)


def banner_falhas(resultados):
    falhas = [r for r in resultados if r.status in ("erro", "timeout")]
    if len(falhas) < max(3, len(resultados) // 2): return
    comuns = Counter((r.erro or "")[:90] for r in falhas).most_common(3)
    st.error(f"{len(falhas)} fontes falharam. Causas principais:\n\n" + "\n".join(f"- **{n}×** `{msg}`" for msg, n in comuns))


with aviso_slot:
    banner_falhas(resultados)

# ==========================================
# 5) FILTROS DE RESULTADO (continuação do painel esquerdo)
# ==========================================
filtradas = vagas_todas
with filtros_pos:
    if vagas_todas:
        st.markdown("<div class='f-sec'>🗓️ Publicação e ordem</div>", unsafe_allow_html=True)
        periodo = st.selectbox("Data de publicação", ["Qualquer data", "Últimos 3 dias", "Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias"],
                               key=f"f_per_{rid}", label_visibility="collapsed")
        ordem = st.selectbox("Classificação", ["Relevância", "Mais recentes"], key=f"f_ord_{rid}", label_visibility="collapsed")
        origens = sorted({v["origem"] for v in vagas_todas})
        escolhidas = st.multiselect("Filtrar por Fonte", origens, default=origens, key=f"f_ori_{rid}")

        dias_max = {"Últimos 3 dias": 3, "Últimos 7 dias": 7, "Últimos 15 dias": 15, "Últimos 30 dias": 30}.get(periodo)
        filtradas = [v for v in vagas_todas
                     if v["origem"] in escolhidas and (not mods or modalidade(v) in mods)
                     and (dias_max is None or (core.idade_dias(v.get("data")) is not None and core.idade_dias(v["data"]) <= dias_max))]
        if ordem == "Mais recentes":
            filtradas = sorted(filtradas, key=lambda v: v.get("data") or core.MIN_DATA, reverse=True)

        if chave and filtradas and st.button("✨ Gerar Insights de Perfil (Gemini AI)", use_container_width=True):
            try:
                with st.spinner("Analisando competências..."):
                    analisar_com_gemini(filtradas[:12], st.session_state.get("termo_busca", ""),
                                        st.session_state.get("nivel_busca", "(qualquer)"), chave)
            except Exception as e:
                st.warning(f"Erro na IA: {str(e)[:120]}")

# ==========================================
# 6) LISTA DE VAGAS (centro)
# ==========================================
with col_lista:
    if vagas_todas:
        st.caption(f"{len(filtradas)} resultados processados em {st.session_state.get('tempo', 0):.1f}s")
    painel = st.container(height=680)
    if not vagas_todas and not resultados:
        painel.markdown(bv.html_boas_vindas(len(fontes_ativas), FREE_DAILY_LIMIT), unsafe_allow_html=True)
    elif not vagas_todas:
        painel.info("Utilize a barra superior para realizar uma nova pesquisa.")
    elif not filtradas:
        painel.info("Nenhuma vaga atende aos filtros atuais.")

    n_mostrar = st.session_state.get("mostrar_n", 15)
    for v in filtradas[:n_mostrar]:
        dias = core.idade_dias(v.get("data"))
        descricao = (v.get("analise") or v.get("resumo") or "")[:240]
        link = v["link"] if core.eh_http(v.get("link")) else "#"
        badge_cls = "badge-source badge-global" if v.get("grupo") in ("Global", "Empresas") else "badge-source"
        origem_txt = f'{v["origem"]} · {v["grupo"]}' if v.get("grupo") else v["origem"]
        tambem = f'<span class="badge-also">também via {esc(", ".join(v["tambem"]))}</span>' if v.get("tambem") else ""
        desc_html = f'<div class="job-desc">{esc(descricao)}{"…" if len(descricao) >= 240 else ""}</div>' if descricao else ""

        painel.markdown(
            f'<div class="job-card">'
            f'<div class="job-top"><div style="flex:1;"><div class="job-title">{esc(v["titulo"])}</div>'
            f'<div class="job-company">{esc(v["empresa"])} &middot; {esc(v["local"])}</div></div>'
            f'<div class="{classe_idade(dias)} age">🕒 {texto_idade(dias)}</div></div>'
            f'{desc_html}'
            f'<div class="job-bottom"><div><span class="{badge_cls}">{esc(origem_txt)}</span>{tambem}</div>'
            f'<a href="{esc(link)}" target="_blank" rel="noopener noreferrer" class="btn-apply">Candidatar-se</a>'
            f'</div></div>', unsafe_allow_html=True)

    if len(filtradas) > n_mostrar:
        if st.button(f"Carregar mais resultados ({len(filtradas) - n_mostrar})", use_container_width=True):
            st.session_state.mostrar_n = n_mostrar + 15
            st.rerun()

# ==========================================
# 7) MAPA (direita)
# ==========================================
with col_mapa:
    with st.container(key="mapa_card"):
        com_pino = sum(1 for v in filtradas if v.get("lat"))
        st.markdown(f"<div class='map-head'>📍 Mapa · {com_pino} vagas</div>", unsafe_allow_html=True)
        chave_mapa = (tuple(v["link"] for v in filtradas), aproximar)
        if st.session_state.get("_mapa_chave") != chave_mapa:
            st.session_state["_mapa_chave"], st.session_state["_mapa"] = chave_mapa, montar_mapa(filtradas, aproximar)
        st_folium(st.session_state["_mapa"], height=560, use_container_width=True, returned_objects=[], key="mapa")
        st.markdown(
            "<div class='legend'>"
            "<span><i class='dot' style='background:#10B981'></i>verde recente</span>"
            "<span><i class='dot' style='background:#F59E0B'></i>âmbar médio</span>"
            "<span><i class='dot' style='background:#94A3B8'></i>cinza antigo</span></div>",
            unsafe_allow_html=True)

rodape_inovhia()
