"""Kit visual do Sistema TAZZIN: faixa de título, cartões de indicador e selos.

O desenho segue o padrão das telas de Pós-Vendas do BI (faixa de título com
área e subtítulo, cartões com borda colorida, selo de situação, perguntas em
português acima de cada quadro), na identidade TAZZIN: marinho, grafite, verde
só para o que é positivo e Poppins.

Duas partes:
  * ``aplicar_estilo()`` — CSS global, chamado por ``apply_branding``. Faz todo
    ``st.metric``, bloco com borda, aba e tabela das telas já nascerem no
    padrão, sem tocar em cada uma.
  * ``cabecalho()``, ``kpi()``, ``kpis()``, ``selo()`` — componentes para as
    telas que querem o desenho completo.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from app.core.branding import AZUL, CINZA_CLARO, CINZA_MEDIO, GRAFITE, MARINHO, VERDE

VERMELHO = "#E5484D"
AMBAR = "#F2A900"
BORDA = "#1E3247"        # marinho um passo acima do fundo
AZUL_FAIXA = "#14304D"   # ponta clara do degradê da faixa de título

_TONS = {
    "ok": VERDE,
    "atencao": AMBAR,
    "ruim": VERMELHO,
    "neutro": "#A8B3C4",
    "info": AZUL,
}

_CSS = f"""
<style>
  /* Respiro e largura de leitura */
  .block-container {{ padding-top: 2.2rem; max-width: 1280px; }}

  /* Indicadores nativos (st.metric) viram cartões do padrão */
  div[data-testid="stMetric"] {{
    background: {GRAFITE};
    border: 1px solid {BORDA};
    border-left: 5px solid {AZUL};
    border-radius: 10px;
    padding: 14px 16px 12px 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,.25);
    height: 100%;
  }}
  div[data-testid="stMetricLabel"] p {{
    font-size: .72rem; font-weight: 700; letter-spacing: .6px;
    text-transform: uppercase; color: {CINZA_CLARO}; opacity: .85;
  }}
  div[data-testid="stMetricValue"] {{
    font-size: 1.4rem; font-weight: 700; line-height: 1.15;
  }}

  /* Blocos com borda (container(border=True)) e tabelas */
  div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 12px; border-color: {BORDA};
    background: rgba(31,41,55,.45);
  }}
  div[data-testid="stDataFrame"] {{
    border: 1px solid {BORDA}; border-radius: 10px; overflow: hidden;
  }}

  /* Títulos de seção: pergunta em português, com um filete verde */
  .block-container h3 {{
    font-size: 1.12rem; font-weight: 600; margin-top: .4rem;
    padding-left: 10px; border-left: 3px solid {VERDE};
  }}
  .block-container h4 {{ font-size: 1rem; font-weight: 600; }}

  /* Abas mais limpas */
  button[data-baseweb="tab"] {{ font-weight: 600; }}

  /* Faixa de título */
  .tz-faixa {{
    background: linear-gradient(135deg, {AZUL_FAIXA} 0%, {MARINHO} 100%);
    border: 1px solid {BORDA}; border-bottom: 3px solid {VERDE};
    border-radius: 14px; padding: 20px 26px; margin: 0 0 16px 0;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 10px;
  }}
  .tz-faixa .tz-area {{
    font-size: .72rem; font-weight: 700; color: {VERDE};
    text-transform: uppercase; letter-spacing: 1.2px;
  }}
  .tz-faixa h1 {{
    color: #fff; font-weight: 700; font-size: 1.7rem; margin: 4px 0 0 0; padding: 0;
  }}
  .tz-faixa .tz-sub {{ font-size: .88rem; color: #9DB7D5; margin-top: 4px; max-width: 760px; }}
  .tz-faixa .tz-dir {{ text-align: right; }}
  .tz-faixa .tz-dir small {{
    display: block; font-size: .68rem; color: #9DB7D5; text-transform: uppercase;
    letter-spacing: .6px;
  }}
  .tz-faixa .tz-dir b {{ font-size: 1.05rem; color: #fff; font-weight: 700; }}

  /* Cartão de indicador */
  .tz-kpi {{
    background: {GRAFITE}; border: 1px solid {BORDA}; border-radius: 10px;
    padding: 14px 16px; height: 100%; box-shadow: 0 2px 10px rgba(0,0,0,.25);
  }}
  .tz-kpi .tz-rot {{
    font-size: .72rem; font-weight: 700; letter-spacing: .6px;
    text-transform: uppercase; color: {CINZA_CLARO}; opacity: .85;
  }}
  .tz-kpi .tz-val {{ font-size: 1.4rem; font-weight: 700; margin: 6px 0 2px; line-height: 1.1; }}
  .tz-kpi .tz-nota {{ font-size: .78rem; color: {CINZA_MEDIO}; margin-top: 6px; }}
  .tz-selo {{
    display: inline-block; border-radius: 20px; padding: 2px 10px;
    font-size: .72rem; font-weight: 700;
  }}
</style>
"""


def aplicar_estilo() -> None:
    """Injeta o CSS do padrão visual (uma vez por execução da página)."""
    st.markdown(_CSS, unsafe_allow_html=True)


def selo(texto: str, tom: str = "neutro") -> str:
    """Etiqueta arredondada de situação. ``tom``: ok, atencao, ruim, neutro, info."""
    cor = _TONS.get(tom, CINZA_MEDIO)
    return (f"<span class='tz-selo' style='background:{cor}26;color:{cor};'>"
            f"{escape(texto)}</span>")


def cabecalho(area: str, titulo: str, subtitulo: str = "",
              direita_rotulo: str = "", direita_valor: str = "") -> None:
    """Faixa de título: área em verde, título, subtítulo e um dado à direita."""
    dir_html = ""
    if direita_valor:
        dir_html = (f"<div class='tz-dir'><small>{escape(direita_rotulo)}</small>"
                    f"<b>{escape(direita_valor)}</b></div>")
    sub = f"<div class='tz-sub'>{escape(subtitulo)}</div>" if subtitulo else ""
    st.markdown(
        f"<div class='tz-faixa'><div><div class='tz-area'>{escape(area)}</div>"
        f"<h1>{escape(titulo)}</h1>{sub}</div>{dir_html}</div>",
        unsafe_allow_html=True,
    )


def kpi(rotulo: str, valor: str, nota: str = "", tom: str = "info",
        situacao: str = "", situacao_tom: str | None = None) -> str:
    """HTML de um cartão: rótulo, número grande na cor do tom, selo e nota."""
    cor = _TONS.get(tom, AZUL)
    selo_html = f"<div style='margin-top:6px;'>{selo(situacao, situacao_tom or tom)}</div>" if situacao else ""
    nota_html = f"<div class='tz-nota'>{escape(nota)}</div>" if nota else ""
    return (f"<div class='tz-kpi' style='border-left:5px solid {cor};'>"
            f"<div class='tz-rot'>{escape(rotulo)}</div>"
            f"<div class='tz-val' style='color:{cor};'>{escape(valor)}</div>"
            f"{selo_html}{nota_html}</div>")


def kpis(cartoes: list[dict], por_linha: int = 4) -> None:
    """Desenha os cartões em linhas de ``por_linha``. Cada item vira ``kpi(**item)``."""
    for inicio in range(0, len(cartoes), por_linha):
        linha = cartoes[inicio:inicio + por_linha]
        for coluna, cartao in zip(st.columns(por_linha), linha):
            coluna.markdown(kpi(**cartao), unsafe_allow_html=True)
        st.write("")


# ── Tabelas coloridas ────────────────────────────────────────────────────────
# Palavras de situação que ganham cor sozinhas, para a diferença entre uma linha
# e outra aparecer sem ler. Verde só para o que é bom (mesma regra dos gráficos).
_SITUACAO = {
    VERDE: {"ativo", "ativa", "ok", "aprovado", "aprovada", "concluído", "concluida", "concluída",
            "promotor", "resolvido", "reativado", "voltou a comprar", "confirmada", "no prazo", "em dia", "quente", "dentro da meta", "positivo", "pago"},
    AMBAR: {"morna", "atenção", "atencao", "a vencer", "pendente", "em andamento", "planejado",
            "rascunho", "observar", "em contato", "leve", "média", "media", "em risco"},
    VERMELHO: {"vencida", "vencido", "atrasado", "atrasada", "reprovado", "reprovada", "crítico",
               "critico", "negativo", "fora da meta", "inativo", "inativa", "detrator", "grave", "alta", "perdido"},
    AZUL: {"fria", "em análise", "em analise", "novo", "nova", "neutro", "baixa", "médio"},
}
_TOM_DE = {v.lower(): cor for cor, nomes in _SITUACAO.items() for v in nomes}
_NAO_ESCALAR = ("id", "código", "codigo", "ncm", "cnpj", "ano", "mês", "mes", "cep", "ddd")
_FUNDO_PAR = "#1B2636"
_FUNDO_IMPAR = "#172130"


def _mistura(cor_a: str, cor_b: str, t: float) -> str:
    a = [int(cor_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(cor_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def tabela(df, **kwargs) -> None:
    """``st.dataframe`` no padrão TAZZIN: linhas alternadas, 1ª coluna em negrito,
    situação em cor (verde/âmbar/vermelho), saldo positivo/negativo em verde/vermelho
    e coluna numérica com intensidade proporcional ao valor.

    Aceita os mesmos argumentos do ``st.dataframe``. Se já vier um ``Styler``
    ou algo que não seja ``DataFrame``, só repassa.
    """
    import pandas as pd

    kwargs.setdefault("hide_index", True)
    kwargs.setdefault("width", "stretch")
    if isinstance(df, list):
        df = pd.DataFrame(df)
    if not isinstance(df, pd.DataFrame) or df.empty or df.shape[1] == 0:
        st.dataframe(df, **kwargs)
        return

    numericas = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
                 and not pd.api.types.is_bool_dtype(df[c])
                 and not any(k in str(c).lower() for k in _NAO_ESCALAR)]
    primeira = df.columns[0]

    def linha(row):
        fundo = _FUNDO_PAR if row.name % 2 == 0 else _FUNDO_IMPAR
        return [f"background-color:{fundo};" for _ in row]

    def coluna(serie):
        nome = serie.name
        estilos = [""] * len(serie)
        if nome == primeira:
            estilos = ["font-weight:700;"] * len(serie)
        if nome in numericas:
            vals = pd.to_numeric(serie, errors="coerce")
            if vals.min() < 0 < vals.max() or (vals.min() < 0 and vals.max() <= 0):
                estilos = [("color:%s;font-weight:600;" % (VERDE if v > 0 else VERMELHO if v < 0 else CINZA_MEDIO))
                           if pd.notna(v) else "" for v in vals]
            elif vals.max() and vals.max() > 0 and vals.nunique() > 3:
                estilos = [f"background-color:{_mistura('#172130', '#2E6DA4', 0.75 * max(v, 0) / vals.max())};"
                           if pd.notna(v) else "" for v in vals]
        else:
            tons = [_TOM_DE.get(str(v).strip().lower()) for v in serie]
            if any(tons):
                estilos = [f"color:{t};font-weight:700;" if t else e for t, e in zip(tons, estilos)]
        return estilos

    try:
        estilo = df.reset_index(drop=True).style.apply(linha, axis=1).apply(coluna, axis=0)
        st.dataframe(estilo, **kwargs)
    except Exception:  # noqa: BLE001 — estilo nunca pode derrubar a tela
        st.dataframe(df, **kwargs)
