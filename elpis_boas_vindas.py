# Élpis — tela de boas-vindas (aparece enquanto o usuário ainda não buscou nada)
# © 2026 INOVHIA Desenvolvimento Tecnológico.
#
# Uso no app (3 pontos):
#   import elpis_boas_vindas as bv
#   st.markdown(bv.CSS, unsafe_allow_html=True)                       # 1) junto do CSS do app
#   painel.markdown(bv.html_boas_vindas(len(fontes_ativas), FREE_DAILY_LIMIT),
#                   unsafe_allow_html=True)                           # 2) no lugar do st.info "Informe o Cargo…"
#   st.markdown(bv.ESCONDER, unsafe_allow_html=True)                  # 3) no início da busca (some na hora)
from __future__ import annotations

CSS = """<style>
.elpis-welcome { background: linear-gradient(145deg, #FFFFFF 0%, #F1F5F9 100%); border: 1px solid #E5E7EB;
    border-radius: 14px; padding: 28px 30px 22px; min-height: 470px; display: flex; flex-direction: column; justify-content: center; }
.elpis-welcome .ew-kicker { font-size: 11.5px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #B45309; }
.elpis-welcome .ew-title { font-size: 28px; font-weight: 800; line-height: 1.2; color: #0F2A4A; margin: 8px 0 14px; }
.elpis-welcome .ew-title span { color: #D97706; }
.elpis-welcome .ew-text { font-size: 14.5px; line-height: 1.65; color: #374151; margin: 0 0 20px; }
.elpis-welcome .ew-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); gap: 12px; margin-bottom: 20px; }
.elpis-welcome .ew-step { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 14px 14px 12px; }
.elpis-welcome .ew-num { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px;
    border-radius: 9999px; background: #F59E0B; color: #0F2A4A; font-size: 12.5px; font-weight: 800; margin-right: 8px; }
.elpis-welcome .ew-step b { font-size: 14px; color: #0F2A4A; }
.elpis-welcome .ew-step small { display: block; font-size: 12.5px; line-height: 1.45; color: #6B7280; margin-top: 8px; }
.elpis-welcome .ew-quote { border-left: 3px solid #F59E0B; padding: 2px 0 2px 12px; font-size: 14.5px; font-style: italic; color: #0F2A4A; }
.elpis-welcome .ew-foot { margin-top: 16px; font-size: 12.5px; color: #6B7280; }
@media (max-width: 1400px) {
  .elpis-welcome { padding: 18px 20px 16px; min-height: 0; }
  .elpis-welcome .ew-title { font-size: 22px; margin: 6px 0 10px; }
  .elpis-welcome .ew-text { font-size: 13px; line-height: 1.5; margin-bottom: 14px; }
  .elpis-welcome .ew-steps { gap: 8px; margin-bottom: 14px; }
  .elpis-welcome .ew-step { padding: 9px 12px; }
  .elpis-welcome .ew-step small { display: none; }
  .elpis-welcome .ew-foot { margin-top: 10px; }
}
</style>"""

# Injetado no começo da busca: esconde na hora a tela de boas-vindas que ainda está na tela (o Streamlit
# mantém os elementos antigos visíveis até o fim da execução, e a busca pode levar vários segundos).
ESCONDER = "<style>.elpis-welcome { display: none !important; }</style>"


def html_boas_vindas(n_fontes: int, limite_gratis: int) -> str:
    """HTML numa única linha por bloco (linhas em branco/recuo quebrariam o Markdown do Streamlit)."""
    n = max(0, int(n_fontes))
    fontes = f"{n} fontes" if n != 1 else "1 fonte"
    return (
        '<div class="elpis-welcome">'
        '<div class="ew-kicker">Élpis · do grego <i>elpís</i>, “esperança”</div>'
        '<div class="ew-title">Toda grande carreira começa com <span>uma busca</span>.</div>'
        '<p class="ew-text">A Élpis consulta várias plataformas de emprego ao mesmo tempo, reúne as vagas em um só lugar, '
        'remove as repetidas e ordena pelas mais próximas do que você procura. Menos tempo procurando, '
        'mais tempo se preparando para a próxima conversa.</p>'
        '<div class="ew-steps">'
        '<div class="ew-step"><span class="ew-num">1</span><b>Diga o que procura</b>'
        '<small>Cargo ou função e, se quiser, cidade e nível.</small></div>'
        '<div class="ew-step"><span class="ew-num">2</span><b>A Élpis trabalha</b>'
        f'<small>{fontes} consultadas em paralelo, sem abrir um site por vez.</small></div>'
        '<div class="ew-step"><span class="ew-num">3</span><b>Escolha com clareza</b>'
        '<small>Filtre por período, veja a origem de cada vaga e o mapa.</small></div>'
        '</div>'
        '<div class="ew-quote">A esperança é o primeiro passo. A candidatura é o segundo.</div>'
        f'<div class="ew-foot">Digite o cargo na barra acima e clique em <b>Buscar</b>. '
        f'Gratuito: até {int(limite_gratis)} buscas por sessão, sem senha.</div>'
        '</div>'
    )
