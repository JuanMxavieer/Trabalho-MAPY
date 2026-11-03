import io
import os

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dashboard IBGE - Áreas Gerais de Formação",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARQUIVO_PADRAO = "Tabela_3_Areas_gerais_de_formacao_na_graduacao.xlsx"
REGIOES = ["Brasil", "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]

GRUPOS = {
    "total": {"total": 1, "mulheres": 3, "col_total": "total_graduados", "col_mulheres": "mulheres_total", "col_pct": "pct_mulheres_total"},
    "stem": {"total": 4, "mulheres": 6, "col_total": "stem_total", "col_mulheres": "mulheres_stem", "col_pct": "pct_mulheres_stem"},
    "saude": {"total": 7, "mulheres": 9, "col_total": "saude_total", "col_mulheres": "mulheres_saude", "col_pct": "pct_mulheres_saude"},
}

NOMES_AREAS = {
    "pct_mulheres_total": "Graduação Total",
    "pct_mulheres_stem": "STEM (Exatas/Tecnologia)",
    "pct_mulheres_saude": "Saúde e Educação",
}


NOTICIAS = [
    {
        "titulo": "Mulheres são maioria na formação científica e somam 57% dos titulados na pós-graduação",
        "fonte": "Sul21",
        "data": "12/02/2026",
        "resumo": "Segundo o Plano Nacional de Pós-Graduação 2025-2029, elas são maioria entre estudantes e titulados, mas ocupam apenas 43% do corpo docente da pós-graduação.",
        "link": "https://sul21.com.br/?p=286152",
    },
    {
        "titulo": "Mulheres já ocupam 49% da produção científica no Brasil, aponta pesquisa",
        "fonte": "Viva",
        "data": "11/02/2026",
        "resumo": "O Brasil está entre os países com maior presença feminina na produção científica, com presença já consolidada em áreas como saúde e ciências biológicas.",
        "link": "https://viva.com.br/carreira-e-educacao/mulheres-ja-ocupam-49-da-producao-cientifica-no-brasil-aponta-pesquisa.html",
    },
    {
        "titulo": "O papel decisivo das mulheres nas comunidades científicas e tecnológicas",
        "fonte": "Portal da Indústria",
        "data": "",
        "resumo": "Cita o Censo da Educação Superior de 2021: mulheres eram 13,3% das matrículas presenciais em Computação e TIC e 21,6% em Engenharia, mas permanecem mais tempo nas graduações STEM (77,5% contra 73% dos homens).",
        "link": "https://noticias.portaldaindustria.com.br/noticias/inovacao-e-tecnologia/o-papel-decisivo-das-mulheres-nas-comunidades-cientificas-e-tecnologicas/",
    },
    {
        "titulo": "Da Escola ao Mercado de Trabalho: sub-representação feminina em STEM no Brasil",
        "fonte": "SBC - Women in Information Technology (WIT 2026)",
        "data": "19/07/2026",
        "resumo": "Estudo que acompanha a participação feminina em STEM entre 2020 e 2025 usando Censo Escolar, Censo da Educação Superior, Plataforma Lattes e PNADC/IBGE.",
        "link": "https://sol.sbc.org.br/index.php/wit/article/view/43345",
    },
    {
        "titulo": "Trajetórias Ocupacionais de Mulheres em STEM no Brasil",
        "fonte": "Ministério do Trabalho e Emprego (gov.br)",
        "data": "03/2025",
        "resumo": "Apresentação mostra que, entre 2010 e 2022, mulheres continuam concentradas em áreas de cuidados e humanas, e que STEM tem os maiores salários e a maior diferença entre homens e mulheres.",
        "link": "https://www.gov.br/trabalho-e-emprego/pt-br/noticias-e-conteudo/2025/marco/desafios-da-mulher-no-mercado-de-trabalho-desigualdade-de-genero-e-racismo-persistem/ApresentaoMulheresemSTEMMarianaEugenioAlmeida.pdf/@@download/file",
    },
]


def ler_bruto(conteudo: bytes, nome: str) -> pd.DataFrame:
    buffer = io.BytesIO(conteudo)
    if nome.lower().endswith(".csv"):
        return pd.read_csv(buffer, header=None)
    return pd.read_excel(buffer, header=None)


@st.cache_data
def carregar_formacao(conteudo: bytes, nome: str) -> pd.DataFrame:
    bruto = ler_bruto(conteudo, nome).iloc[3:36].reset_index(drop=True)

    df = pd.DataFrame({"uf_regiao": bruto[0].astype(str).str.strip()})

    for g in GRUPOS.values():
        total = pd.to_numeric(bruto[g["total"]], errors="coerce")
        mulheres = pd.to_numeric(bruto[g["mulheres"]], errors="coerce")
        df[g["col_total"]] = total
        df[g["col_mulheres"]] = mulheres
        df[g["col_pct"]] = (mulheres / total.where(total > 0) * 100).round(2)

    if "Brasil" not in df["uf_regiao"].values:
        raise ValueError("Linha 'Brasil' não encontrada. Verifique o formato da planilha.")

    return df


st.sidebar.title("📌 Menu & Filtros")
st.sidebar.subheader("📂 Arquivo de entrada")
arquivo = st.sidebar.file_uploader("Upload Tabela 3 (Formação):", type=["xls", "xlsx", "csv"])

conteudo, nome = None, None
if arquivo is not None:
    conteudo, nome = arquivo.getvalue(), arquivo.name
elif os.path.exists(ARQUIVO_PADRAO):
    with open(ARQUIVO_PADRAO, "rb") as f:
        conteudo, nome = f.read(), ARQUIVO_PADRAO

if conteudo is None:
    st.warning("⚠️ Nenhum arquivo encontrado.")
    st.info(f"Coloque `{ARQUIVO_PADRAO}` na pasta do app ou use o upload na barra lateral.")
    st.stop()

try:
    df_formacao = carregar_formacao(conteudo, nome)
except Exception as e:
    st.sidebar.error(f"Erro ao carregar a tabela: {e}")
    st.stop()

br = df_formacao[df_formacao["uf_regiao"] == "Brasil"].iloc[0]

st.sidebar.markdown("---")
pagina = st.sidebar.radio("Selecione a Visualização:", ["🏠 Visão Geral", "🎓 Formação Acadêmica", "📰 Notícias"])

st.sidebar.markdown("---")
tipo_visao = st.sidebar.radio("Filtrar recorte:", ["Apenas Estados (27 UFs)", "Apenas Regiões e Brasil"])

if tipo_visao == "Apenas Estados (27 UFs)":
    df_fil = df_formacao[~df_formacao["uf_regiao"].isin(REGIOES)]
else:
    df_fil = df_formacao[df_formacao["uf_regiao"].isin(REGIOES)]

locais_disp = df_fil["uf_regiao"].tolist()
locais_sel = st.sidebar.multiselect("Filtrar UFs / Regiões:", locais_disp, default=locais_disp)
df_fil = df_fil[df_fil["uf_regiao"].isin(locais_sel)]

if df_fil.empty:
    st.warning("Selecione ao menos uma localidade na barra lateral.")
    st.stop()


if pagina == "🏠 Visão Geral":
    st.title("📊 Painel de Análise Social IBGE - Áreas Gerais de Formação")
    st.markdown("Dados da Tabela 3 do IBGE, tratados com **Pandas**.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de graduados (Brasil)", f"{br['total_graduados']:,.0f}".replace(",", "."))
    col2.metric("% Mulheres (total)", f"{br['pct_mulheres_total']:.1f}%")
    col3.metric("% Mulheres em STEM", f"{br['pct_mulheres_stem']:.1f}%")
    col4.metric("% Mulheres em Saúde/Educação", f"{br['pct_mulheres_saude']:.1f}%")

    st.markdown("---")
    st.subheader("📋 Tabela tratada")
    st.dataframe(df_fil, width="stretch")


elif pagina == "🎓 Formação Acadêmica":
    st.title("🎓 Proporção de Mulheres na Graduação Superior")

    df_melt = df_fil.melt(
        id_vars=["uf_regiao"],
        value_vars=list(NOMES_AREAS),
        var_name="Área",
        value_name="Percentual",
    )
    df_melt["Área"] = df_melt["Área"].map(NOMES_AREAS)

    st.subheader("1. % de Mulheres por Área e Localidade")
    fig_barras = px.bar(
        df_melt,
        x="uf_regiao",
        y="Percentual",
        color="Área",
        barmode="group",
        labels={"Percentual": "% de Mulheres", "uf_regiao": "Localidade"},
    )
    fig_barras.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Paridade (50%)")
    st.plotly_chart(fig_barras, width="stretch")

    st.subheader("2. Distribuição por Área (Boxplot)")
    fig_box = px.box(df_melt, x="Área", y="Percentual", color="Área", points="all")
    fig_box.add_hline(y=50, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_box, width="stretch")

    st.subheader("3. Ranking de Mulheres em STEM")
    ranking = df_fil.dropna(subset=["pct_mulheres_stem"]).sort_values("pct_mulheres_stem")
    fig_rank = px.bar(
        ranking,
        x="pct_mulheres_stem",
        y="uf_regiao",
        orientation="h",
        text_auto=".1f",
        labels={"pct_mulheres_stem": "% de Mulheres em STEM", "uf_regiao": "Localidade"},
        color="pct_mulheres_stem",
        color_continuous_scale="Blues",
    )
    fig_rank.add_vline(
        x=br["pct_mulheres_stem"],
        line_dash="dash",
        line_color="red",
        annotation_text=f"Brasil ({br['pct_mulheres_stem']:.1f}%)",
    )
    st.plotly_chart(fig_rank, width="stretch")


else:
    st.title("📰 Notícias")
    st.caption("Mulheres na ciência, na tecnologia e no ensino superior no Brasil.")

    for n in NOTICIAS:
        with st.container(border=True):
            st.subheader(n["titulo"])
            st.caption(" · ".join(filter(None, [n["fonte"], n["data"]])))
            st.write(n["resumo"])
            st.link_button("Ler matéria completa", n["link"])
