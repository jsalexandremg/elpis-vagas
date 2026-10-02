st.markdown("""
<style>
/* =========================================================
   DESIGN SYSTEM ÉLPIS — BLINDAGEM CSS ABSOLUTA
   ========================================================= */
:root {
  --elpis-primary: #142F50;
  --elpis-primary-dark: #0D223A;
  --elpis-orange: #F6A000;
  --elpis-orange-hover: #D98900;
  --status-success: #10B981;
  --status-success-bg: #D2F7EF;
  --status-warning: #F59E0B;
  --status-warning-bg: #FFF2C7;
  --status-neutral: #94A3B8;
  --status-neutral-bg: #E5E7EB;
  --background: #F8FAFC;
  --surface: #FFFFFF;
  --text-primary: #111827;
  --text-secondary: #64748B;
  --text-light: #FFFFFF;
  --border: #E2E8F0;
  --shadow-sm: 0 2px 6px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 8px 24px rgba(15, 23, 42, 0.12);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
}

header[data-testid="stHeader"] {display: none;}
.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}
.stApp { background: var(--background) !important; }

/* ---------- SIDEBAR CORPORATIVA ---------- */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
    font-size: 0.85rem !important;
    color: var(--text-secondary);
}
[data-testid="stSidebar"] hr { border-color: var(--border) !important; margin: 0.8rem 0 !important; }

/* =========================================================
   ANULAÇÃO TOTAL DO VERMELHO: TAGS AZUIS NO MULTISELECT
   ========================================================= */
div[data-baseweb="select"] span[data-baseweb="tag"],
div[data-testid="stMultiSelect"] span[data-baseweb="tag"],
div[data-baseweb="tag"] {
    background-color: var(--elpis-primary) !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 0px 6px !important;
    margin: 2px !important;
    min-height: 22px !important;
}
div[data-baseweb="select"] span[data-baseweb="tag"] span,
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] span,
div[data-baseweb="tag"] span {
    color: var(--text-light) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
}
div[data-baseweb="select"] span[data-baseweb="tag"] svg,
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg,
div[data-baseweb="tag"] svg {
    color: var(--text-light) !important;
    height: 10px !important;
    width: 10px !important;
}
div[data-baseweb="select"] span[data-baseweb="tag"] svg:hover,
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg:hover {
    color: var(--elpis-orange) !important;
}

/* ---------- HEADER / FORM DE BUSCA ---------- */
[data-testid="stForm"] {
    background: var(--elpis-primary) !important;
    border: 0 !important;
    border-radius: var(--radius-md) !important;
    padding: 16px 24px !important;
    box-shadow: var(--shadow-md) !important;
    margin-bottom: 1.5rem !important;
}
[data-testid="stForm"] input, [data-testid="stForm"] div[data-baseweb="select"] > div {
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    min-height: 44px !important;
}
[data-testid="stForm"] button[kind="primary"], [data-testid="stForm"] button[kind="primaryFormSubmit"] {
    background: var(--elpis-orange) !important;
    color: var(--elpis-primary-dark) !important;
    border: 0 !important;
    border-radius: var(--radius-sm) !important;
    min-height: 44px !important;
    font-weight: 800 !important;
    transition: background .2s ease;
}
[data-testid="stForm"] button[kind="primary"] p, [data-testid="stForm"] button[kind="primaryFormSubmit"] p {
    color: var(--elpis-primary-dark) !important;
}
[data-testid="stForm"] button[kind="primary"]:hover, [data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
    background: var(--elpis-orange-hover) !important;
    color: var(--text-light) !important;
}
.elpis-brand { color: var(--elpis-orange); font-weight: 800; font-size: 28px; line-height: 44px;}

/* ---------- CHIPS E CARTÕES ---------- */
.pill-green, .pill-yellow, .pill-gray {
    border-radius: var(--radius-lg) !important;
    padding: 6px 14px !important;
    font-size: 12px !important;
    display: inline-block;
    margin-right: 8px; margin-bottom: 8px;
    white-space: nowrap; font-weight: 600;
}
.pill-green { background: var(--status-success-bg) !important; color: #087F68 !important; border: 1px solid rgba(16, 185, 129, 0.2) !important; }
.pill-yellow { background: var(--status-warning-bg) !important; color: #9A5800 !important; border: 1px solid rgba(245, 158, 11, 0.2) !important; }
.pill-gray { background: var(--status-neutral-bg) !important; color: #475569 !important; border: 1px solid rgba(148, 163, 184, 0.2) !important; }

.job-card {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    padding: 20px !important;
    margin-bottom: 14px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: transform .15s ease, box-shadow .15s ease;
}
.job-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md) !important;
}
.job-title { font-size: 17px; font-weight: 800; color: var(--elpis-primary); line-height: 1.3; }
.job-company { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.badge-source { background: var(--status-info-bg); color: var(--elpis-primary); border-radius: var(--radius-lg); padding: 4px 10px; font-size: 11px; font-weight: 700;}
.badge-also { font-size: 11px; color: var(--status-neutral); margin-left: 8px; }

.btn-apply {
    background: var(--elpis-orange) !important;
    color: var(--elpis-primary-dark) !important;
    border-radius: var(--radius-sm) !important;
    padding: 8px 20px !important;
    font-size: 13px !important;
    font-weight: 800 !important;
    text-decoration: none !important;
    display: inline-block;
    transition: background .2s ease;
}
.btn-apply:hover { background: var(--elpis-orange-hover) !important; color: var(--text-light) !important;}

/* ---------- RODAPÉ CORPORATIVO ---------- */
.elpis-footer {
    background-color: var(--elpis-primary-dark);
    color: var(--border-dark);
    padding: 16px 24px;
    border-top: 3px solid var(--elpis-orange);
    border-radius: var(--radius-sm);
    margin-top: 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8rem;
}
.elpis-footer b { color: var(--text-light); }
.elpis-footer a { color: var(--elpis-orange); text-decoration: none; font-weight: bold;}
</style>
""", unsafe_allow_html=True)
