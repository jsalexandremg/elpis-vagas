# Élpis — Buscador de Vagas com IA (Brasil & Internacional) — v23
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

APP_VERSION = "2026-10-02-v23.10-Blue-Tags-Clean"
st.set_page_config(page_title=f"Élpis {APP_VERSION}", layout="wide", initial_sidebar_state="expanded")

# O Chrome oferece/aplica tradução automática e isso corrompe a interface
st.html("""<script>
try { const d = window.parent.document;
  d.documentElement.setAttribute('lang', 'pt-BR'); d.documentElement.setAttribute('translate', 'no');
  d.documentElement.classList.add('notranslate');
  if (!d.querySelector('meta[name="google"]')) { const m = d.createElement('meta');
    m.name = 'google'; m.content = 'notranslate'; d.head.appendChild(m); } } catch (e) {}
</script>""", unsafe_allow_javascript=True)

st.markdown("""
<style>
    /* O Header NÃO está oculto para garantir que o botão de abrir/fechar a sidebar funcione sempre */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 2rem; padding-right: 2rem; }
    
    /* ========================================================= */
    /* MODO COMPACTO E TAGS AZUIS BLINDADAS NO MULTISELECT       */
    /* ========================================================= */
    
    /* 1. Reduz tamanho geral da fonte na sidebar */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] div.stMarkdown {
        font-size: 0.80rem !important;
    }
    
    /* 2. Forçar a cor AZUL e Tamanho Micro nas Tags de QUALQUER Multiselect */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: #1D4ED8 !important; /* Azul Executivo */
        border: none !important;
        border-radius: 4px !important;
        padding: 0px 6px !important;
        margin: 2px !important;
        height: 22px !important; /* Altura super reduzida */
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span {
        color: #FFFFFF !important; /* Texto branco */
        font-size: 0.70rem !important; /* Fonte legível */
        font-weight: 500 !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] svg {
        color: #FFFFFF !important; /* X branco */
        height: 12px !important;
        width: 12px !important;
    }
    /* Muda a cor ao passar o rato no X */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] svg:hover {
        color: #F87171 !important; 
    }

    /* 3. Reduzir tamanho dos botões na Sidebar para poupar espaço */
    [data-testid="stSidebar"] button {
        min-height: 28px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        font-size: 0.8rem !important;
    }
    
    /* 4. Comprimir as margens invisíveis entre componentes na Sidebar */
    [data-testid="stSidebar"] .element-container {
        margin-bottom: -12px !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 1rem !important;
    }
    hr {
        margin-top: 0.4rem !important;
        margin-bottom: 0.4rem !important;
    }
    /* ========================================================= */

    /* FORMULÁRIO DE BUSCA - TEMA CORPORATIVO RESPONSIVO */
    [data-testid="stForm"] { background-color: #0F2A4A !important; border-radius: 12px; padding: 16px 24px; border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    [data-testid="stForm"] input, [data-testid="stForm"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; color: #111827 !important; border-radius: 8px !important; border: none !important; }
    [data-testid="stForm"] button[kind="primary"], [data-testid="stForm"] button[kind="primaryFormSubmit"] {
        background-color: #F59E0B !important; color: #0F2A4A !important; border: none !important; font-weight: bold !important;
        border-radius: 8px !important; height: 100%; transition: background 0.2s ease; }
    [data-testid="stForm"] button[kind="primary"] p, [data-testid="stForm"] button[kind="primaryFormSubmit"] p { color: #0F2A4A !important; }
    [data-testid="stForm"] button[kind="primary"]:hover, [data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
        background-color: #D97706 !important; }
        
    /* PÍLULAS E CARTÕES DE VAGAS */
    .pill-green, .pill-yellow, .pill-gray { border-radius: 9999px; padding: 4px 12px; font-size: 13px; display: inline-block;
        margin-right: 6px; margin-bottom: 6px; white-space: nowrap; font-weight: 500; }
    .pill-green { background: #D1FAE5; color: #065F46; }
    .pill-yellow { background: #FEF3C7; color: #92400E; }
    .pill-gray { background: #E5E7EB; color: #374151; }
    .job-card { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: transform 0.1s, box-shadow 0.1s; }
    .job-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .job-title { font-size: 16px; font-weight: bold; color: #0F2A4A; line-height: 1.2; }
    .job-company { font-size: 13px; color: #6B7280; margin-top: 4px; }
    .badge-source { background: #E8EEF7; color: #1D4ED8; border-radius: 9999px; padding: 4px 12px; font-size: 12px; font-weight: 500; }
    .badge-global { background: #CCFBF1; color: #115E59; }
    .badge-also { font-size: 11px; color: #6B7280; margin-left: 8px; }
    .btn-apply { background: #F59E0B; color: #0F2A4A !important; border-radius: 8px; padding: 6px 16px; font-size: 13px;
        font-weight: bold; text-decoration: none !important; display: inline-block; text-align: center; transition: background 0.2s; }
    .btn-apply:hover { background: #D97706; color: #FFF !important; }

    /* REGRAS CSS RESPONSIVAS PARA NOTEBOOKS E CELULARES */
    @media (max-width: 1200px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
    }
    @media (max-width: 768px) {
        [data-testid="stForm"] { padding: 12px; }
    }
</style>
""", unsafe_allow_html=True)
st.markdown(bv.CSS, unsafe_allow_html=True)

CREDITO_EMPRESA = "INOVHIA Desenvolvimento Tecnológico"
CREDITO_CONTATO = "Jeferson Alexandre"
CREDITO_TELEFONE = "+55 31 99484-8343"
CREDITO_TEL_LINK = "+5531994848343"

def rodape_inovhia():
    st.markdown("---")
    st.markdown(
        f"<div style='text-align:center;font-size:0.8rem;opacity:0.85;line-height:1.6'>"
        f"Desenvolvido por <b>{html.escape(CREDITO_EMPRESA)}</b><br>"
        f"Contato: {html.escape(CREDITO_CONTATO)} · "
        f"<a href='tel:{CREDITO_TEL_LINK}'>{html.escape(CREDITO_TELEFONE)}</a><br>"
        f"© {datetime.now().year} {html.escape(CREDITO_EMPRESA)}. Todos os direitos reservados.</div>",
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

@st.dialog("Antes de buscar")
def cadastro_dialog():
    st.markdown("Para iniciar a sua sessão gratuita, diga como deseja ser identificado. **Sem senha e sem e-mail.**")
    nome = st.text_input("Nome completo ou profissional", placeholder="Como deseja ser identificado?", key="dlg_nome").strip()
    email = st.text_input("E-mail (opcional)", placeholder="Não será confirmado nesta versão", key="dlg_email").strip()
    aceite = st.checkbox("Aceito os Termos de Uso e a Política de Privacidade para esta sessão.", key="dlg_aceite")
    st.caption("A sessão expira em 24 horas e os registos operacionais são apagados ao encerrar.")
    if st.button("Continuar e buscar", type="primary", use_container_width=True):
        if not nome or not aceite:
            st.warning("Informe o seu nome e aceite a Política de Privacidade.")
        else:
            st.session_state.temporary_session_id = criar_sessao(nome, email)
            st.session_state.busca_pendente = st.session_state.pop("busca_aguardando", None)
            st.rerun()

# ==========================================
# PAINEL LATERAL (CLÁSSICO COMPACTADO E LIMPO)
# ==========================================
sid = st.session_state.get("temporary_session_id")
current_session = sessao_atual(sid)

with st.sidebar:
    if current_session:
        st.caption(f"Sessão: {current_session['nome']}")
        uso_slot = st.empty()
        uso_slot.caption(f"Plano gratuito · {usage_today(sid)}/{FREE_DAILY_LIMIT} buscas realizadas")
        if st.button("Encerrar e apagar sessão", use_container_width=True):
            apagar_sessao(sid)
            st.session_state.pop("temporary_session_id", None)
            st.session_state.vagas, st.session_state.resultados = [], []
            st.rerun()
    else:
        uso_slot = None
        st.caption("Sessão não iniciada: o cadastro rápido aparece na sua primeira busca.")
        
    st.caption(f"Desenvolvido por {CREDITO_EMPRESA}")
    st.markdown("---")
    
    st.header("⚙️ Configuração")
    todas = core.disponiveis()
    fontes_ativas = st.multiselect("Motores ativos", todas, default=todas, help="Fontes marcadas como beta usam páginas sem API oficial.")
    prazo = st.slider("Tempo máximo da busca (s)", 8, 40, 20, help="Fontes que não responderem a tempo são descartadas.")
    
    st.session_state.setdefault("gemini_key", os.getenv("GEMINI_API_KEY", ""))
    st.session_state.setdefault("gemini_connected", False)
    st.session_state.setdefault("gemini_status", "")
    
    chave_digitada = st.text_input("Chave de API Gemini (opcional)", type="password", value=st.session_state["gemini_key"], help="A chave não é gravada em banco de dados.")
    
    col_con, col_des = st.columns(2)
    if col_con.button("Conectar", use_container_width=True):
        chave_t = (chave_digitada or "").strip()
        if not chave_t:
            st.session_state["gemini_status"] = "Informe uma chave Gemini."
            st.session_state["gemini_connected"] = False
        else:
            try:
                from google import genai
                cliente = genai.Client(api_key=chave_t)
                modelos = list(cliente.models.list())
                if modelos:
                    st.session_state["gemini_key"] = chave_t
                    st.session_state["gemini_connected"] = True
                    st.session_state["gemini_status"] = "Gemini conectado com sucesso."
            except Exception as exc:
                st.session_state["gemini_connected"] = False
                st.session_state["gemini_status"] = "Chave recusada ou indisponível."

    if col_des.button("Desconectar", use_container_width=True):
        st.session_state["gemini_key"], st.session_state["gemini_connected"] = "", False
        st.session_state["gemini_status"] = "Chave Gemini desconectada."
        
    if st.session_state["gemini_connected"]: st.success(st.session_state["gemini_status"])
    elif st.session_state["gemini_status"]: st.warning(st.session_state["gemini_status"])
    
    chave = st.session_state["gemini_key"] if st.session_state["gemini_connected"] else ""
    
    aproximar = st.checkbox("Aproximar mapa das vagas", value=True)
    parciais = st.checkbox("Incluir correspondências parciais", value=False)
    
    st.markdown("---")
    with st.expander("👨‍💻 Sobre o Desenvolvedor"):
        st.markdown(
            "**Jeferson Alexandre**\n\n"
            "Especialista em Auditoria, GRC e Engenharia de Dados Aplicada a Controles Internos.\n\n"
            "Formado em **Ciências Contábeis** e **Análise e Desenvolvimento de Sistemas**, com **MBA em Gestão Estratégica**. "
            "Combina a profundidade analítica de Compliance com a agilidade da Tecnologia."
        )

# ==========================================
# FUNÇÕES DE FORMATAÇÃO E IA
# ==========================================
def esc(t): return html.escape(str(t or ""), quote=True)

def classe_idade(dias):
    if dias is None or dias > 10: return "pill-gray"
    return "pill-green" if dias <= 2 else "pill-yellow"

def texto_idade(dias):
    if dias is None or dias > 365: return "Data não informada"
    return "Hoje" if dias == 0 else ("Há 1 dia" if dias == 1 else f"Há {dias} dias")

def chips_html(resultados):
    partes = []
    for r in resultados:
        n, s = len(r.itens), round(r.ms / 1000, 1)
        if r.status == "ok":
            origem_cache = any("cache" in x for x in r.notas)
            classe, txt = "pill-green", f"{r.nome} · {n} · " + ("cache" if origem_cache else f"{s}s")
        elif r.status == "vazio":
            classe, txt = "pill-yellow", f"{r.nome} · 0 vagas"
        elif r.status == "timeout":
            classe, txt = "pill-gray", f"{r.nome} · tempo esgotado"
        else:
            classe, txt = "pill-gray", f"{r.nome} · erro"
        dica = esc((r.erro + " | " if r.erro else "") + " | ".join(r.notas))
        partes.append(f'<span class="{classe}" title="{dica}">{esc(txt)}</span>')
    return f'<div style="margin:5px 0 16px 0;">{"".join(partes)}</div>'

def analisar_com_gemini(vagas, cargo, nivel, chave):
    base = [{"i": i, "titulo": v["titulo"], "empresa": v["empresa"], "local": v["local"]} for i, v in enumerate(vagas)]
    prompt = (f"Busca: {cargo} ({nivel}). Para cada vaga REAL abaixo, escreva 1 frase sobre aderência ao perfil "
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
    for it in json.loads(texto.replace("```json", "").replace("```", "").strip()):
        idx = int(it["i"])
        if 0 <= idx < len(vagas): vagas[idx]["analise"] = it["analise"]

def montar_mapa(vagas, aproximar):
    m = folium.Map(location=[-15.7801, -47.9292], zoom_start=4, min_zoom=2, tiles="OpenStreetMap", world_copy_jump=True, control_scale=False)
    from folium.plugins import MarkerCluster
    grupo = MarkerCluster(options={"maxClusterRadius": 35}).add_to(m)
    pts = []
    for v in vagas:
        if not v.get("lat"): continue
        pts.append([v["lat"], v["lon"]])
        d = core.idade_dias(v.get("data"))
        cor = "#9CA3AF" if d is None or d > 10 else ("#10B981" if d <= 2 else "#F59E0B")
        folium.CircleMarker(location=[v["lat"], v["lon"]], radius=7, color="white", weight=1.5, fill=True,
                            fill_color=cor, fill_opacity=1, tooltip=f"{v['empresa']} | {v['titulo']}"[:120]).add_to(grupo)
    if pts and aproximar: m.fit_bounds(pts, max_zoom=6, padding=(40, 40))
    return m

# ==========================================
# HEADER DE BUSCA PRINCIPAL
# ==========================================
with st.form("search_form"):
    c0, c1, c2, c3, c4 = st.columns([1.2, 3.8, 3, 2, 2])
    with c0: st.markdown("<h3 style='color: #F59E0B; margin-top: 5px;'>Élpis</h3>", unsafe_allow_html=True)
    with c1: cargo = st.text_input("Cargo / Função", placeholder="🏢 Cargo / Função (ex: Auditor Interno, Controller)", label_visibility="collapsed")
    with c2: local = st.text_input("Localidade", placeholder="📍 Localidade (ex: Belo Horizonte, Brasil)", label_visibility="collapsed")
    with c3: nivel = st.selectbox("Nível / Senioridade", ["(qualquer)", "Analista", "Especialista", "Coordenador", "Gerente", "Diretor", "VP"], label_visibility="collapsed")
    with c4: buscar = st.form_submit_button("Buscar", type="primary", use_container_width=True)

# ==========================================
# MOTOR DE EXECUÇÃO E RENDERIZAÇÃO
# ==========================================
params = None
if buscar and not cargo.strip(): st.warning("Informe o Cargo / Função para buscar.")
elif buscar:
    pedido = {"cargo": cargo.strip(), "local": local, "nivel": nivel}
    if current_session is None:
        st.session_state.busca_aguardando = pedido
        cadastro_dialog()
    else: params = pedido

if params is None and current_session is not None:
    params = st.session_state.pop("busca_pendente", None)

if params:
    termo, local, nivel = params["cargo"], params["local"], params["nivel"]
    if usage_today(sid) >= FREE_DAILY_LIMIT:
        st.error(f"Limite gratuito diário atingido.")
        st.stop()
    if not fontes_ativas:
        st.warning("Selecione ao menos um motor na barra lateral.")
        st.stop()
    st.markdown(bv.ESCONDER, unsafe_allow_html=True) 
    brutas, resultados, t0 = [], [], time.perf_counter()

    with st.status("Consultando fontes em paralelo…", expanded=True) as box:
        slot = st.empty()
        for r in core.executar(fontes_ativas, termo, local, prazo=prazo):
            resultados.append(r)
            brutas += r.itens
            slot.markdown(chips_html(resultados), unsafe_allow_html=True)
            box.update(label=f"{len(resultados)}/{len(fontes_ativas)} fontes · {len(brutas)} vagas brutas")
        box.update(label=f"Busca concluída em {time.perf_counter() - t0:.1f}s", state="complete", expanded=False)

    falhas = [r for r in resultados if r.status in ("erro", "timeout")]
    st.session_state.rede = core.verificar_rede() if len(falhas) >= max(3, len(resultados) // 2) else None
    unicas = core.consolidar(brutas, nivel, limite=60, min_exatas=999 if parciais else 5)

    if aproximar and unicas: 
        cache_loc, inicio, consultas = {}, time.perf_counter(), 0
        for v in unicas:
            loc = v["local"]
            if loc not in cache_loc:
                pos = core.geo_offline(loc)
                if not pos and not core.local_generico(loc) and consultas < 5 and time.perf_counter() - inicio < 6:
                    consultas += 1
                    pos = core.geo_nominatim(loc)
                cache_loc[loc] = pos
            v["lat"], v["lon"] = cache_loc[loc] or (None, None)
    else:
        for v in unicas: v["lat"], v["lon"] = None, None

    for v in unicas: v["analise"] = None

    record_usage(sid)
    if uso_slot is not None:
        uso_slot.caption(f"Plano gratuito · {usage_today(sid)}/{FREE_DAILY_LIMIT} buscas realizadas")
        
    st.session_state.update(vagas=unicas, resultados=resultados, tempo=time.perf_counter() - t0,
                            resultado_id=time.time_ns(), mostrar_n=15, termo_busca=termo, nivel_busca=nivel)

vagas_todas = st.session_state["vagas"]
resultados = st.session_state.get("resultados", [])
rid = st.session_state.get("resultado_id", 0)

if resultados: st.markdown(chips_html(resultados), unsafe_allow_html=True)

def banner_falhas(resultados):
    falhas = [r for r in resultados if r.status in ("erro", "timeout")]
    if len(falhas) < max(3, len(resultados) // 2): return
    comuns = Counter((r.erro or "")[:90] for r in falhas).most_common(3)
    st.error(f"{len(falhas)} de {len(resultados)} fontes falharam. Causas:\n\n" + "\n".join(f"- **{n}×** `{msg}`" for msg, n in comuns))
    if st.session_state.get("rede"):
        st.warning("Teste de rede: " + " · ".join(f"{k}: {v}" for k, v in st.session_state["rede"].items()))

banner_falhas(resultados)

filtradas = vagas_todas
if vagas_todas:
    f1, f2, f3, f4 = st.columns([2, 2, 2, 4])
    periodo = f1.selectbox("Período", ["Qualquer data", "Últimos 3 dias", "Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias"], key=f"f_per_{rid}")
    ordem = f2.selectbox("Ordenar por", ["Relevância", "Mais recentes"], key=f"f_ord_{rid}")
    so_remoto = f3.toggle("Somente remotas", key=f"f_rem_{rid}")
    origens = sorted({v["origem"] for v in vagas_todas})
    escolhidas = f4.multiselect("Fontes da Busca Atual", origens, default=origens, key=f"f_ori_{rid}")
    
    dias_max = {"Últimos 3 dias": 3, "Últimos 7 dias": 7, "Últimos 15 dias": 15, "Últimos 30 dias": 30}.get(periodo)
    filtradas = [v for v in vagas_todas
                 if v["origem"] in escolhidas and (not so_remoto or core.eh_remoto(v))
                 and (dias_max is None or (core.idade_dias(v.get("data")) is not None and core.idade_dias(v["data"]) <= dias_max))]
    if ordem == "Mais recentes":
        filtradas = sorted(filtradas, key=lambda v: v.get("data") or core.MIN_DATA, reverse=True)
        
    barra1, barra2 = st.columns([5, 3])
    barra1.caption(f"{len(filtradas)} de {len(vagas_todas)} vagas · processado em {st.session_state.get('tempo', 0):.1f}s")
    if chave and filtradas and barra2.button("✨ Analisar as 12 primeiras com IA", use_container_width=True):
        try:
            with st.spinner("Processando Inteligência Analítica..."):
                analisar_com_gemini(filtradas[:12], st.session_state.get("termo_busca", ""), st.session_state.get("nivel_busca", "(qualquer)"), chave)
        except Exception as e: st.warning(f"Erro na API de IA: {str(e)[:120]}")

col_lista, col_mapa = st.columns([3, 2], gap="large")

with col_lista:
    painel = st.container(height=600)
    if not vagas_todas and not resultados:
        painel.markdown(bv.html_boas_vindas(len(fontes_ativas), FREE_DAILY_LIMIT), unsafe_allow_html=True)
    elif not vagas_todas: painel.info("Informe o Cargo / Função desejada e clique em Buscar.")
    elif not filtradas: painel.info("Nenhuma vaga com os filtros aplicados.")
    
    n_mostrar = st.session_state.get("mostrar_n", 15)
    for v in filtradas[:n_mostrar]:
        dias = core.idade_dias(v.get("data"))
        descricao = (v.get("analise") or v.get("resumo") or "")[:240]
        link = v["link"] if core.eh_http(v.get("link")) else "#"
        badge_cls = "badge-source badge-global" if v.get("grupo") in ("Global", "Empresas") else "badge-source"
        tambem = f'<span class="badge-also">também em {esc(", ".join(v["tambem"]))}</span>' if v.get("tambem") else ""
        
        painel.markdown(
            f'<div class="job-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">'
            f'<div style="flex:1;"><div class="job-title">{esc(v["titulo"])}</div>'
            f'<div class="job-company">{esc(v["empresa"])} &middot; {esc(v["local"])}</div></div>'
            f'<div class="{classe_idade(dias)}">{texto_idade(dias)}</div></div>'
            f'<div style="font-size:13px;color:#4B5563;margin:10px 0 12px;line-height:1.4;">{esc(descricao)}</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;">'
            f'<div><span class="{badge_cls}">{esc(v["origem"])}</span>{tambem}</div>'
            f'<a href="{esc(link)}" target="_blank" rel="noopener noreferrer" class="btn-apply">Candidatar-se</a>'
            f'</div></div>', unsafe_allow_html=True)
            
    if len(filtradas) > n_mostrar:
        if st.button(f"Mostrar mais ({len(filtradas) - n_mostrar} restantes)", use_container_width=True):
            st.session_state.mostrar_n = n_mostrar + 15
            st.rerun()
with col_mapa:
    com_pino = sum(1 for v in filtradas if v.get("lat"))
    st.markdown(f"<div style='font-size:16px; font-weight:600; color:#0F2A4A; margin-bottom:4px;'>"
                f"Mapa &middot; {com_pino} de {len(filtradas)} vagas localizadas</div>", unsafe_allow_html=True)
    st.caption("Verde: até 2 dias · Âmbar: até 10 dias · Cinza: mais antiga ou sem data.")
    chave_mapa = (tuple(v["link"] for v in filtradas), aproximar)
    if st.session_state.get("_mapa_chave") != chave_mapa:
        st.session_state["_mapa_chave"], st.session_state["_mapa"] = chave_mapa, montar_mapa(filtradas, aproximar)
    st_folium(st.session_state["_mapa"], height=550, use_container_width=True, returned_objects=[], key="mapa")

if resultados:
    muitas = sum(r.status in ("erro", "timeout") for r in resultados) >= max(3, len(resultados) // 2)
    with st.expander("🔎 Diagnóstico das fontes (o que cada motor respondeu)", expanded=muitas):
        st.dataframe([{
            "Fonte": r.nome, "Grupo": r.grupo, "Situação": {"ok": "OK", "vazio": "Sem vagas", "erro": "Erro", "timeout": "Tempo esgotado"}[r.status],
            "Vagas": len(r.itens), "Tempo (s)": round(r.ms / 1000, 1), "Detalhe": (r.erro + " | " if r.erro else "") + " | ".join(r.notas),
        } for r in resultados], hide_index=True, width="stretch")

rodape_inovhia()
