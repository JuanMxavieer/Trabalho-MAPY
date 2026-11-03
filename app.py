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
pagina = st.sidebar.radio("Selecione a Visualização:", ["🏠 Visão Geral", "🎓 Formação Acadêmica"])

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


else:
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
