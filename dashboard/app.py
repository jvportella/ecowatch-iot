import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from database import get_connection
from export_reports import exportar_leituras_csv


st.set_page_config(
    page_title="EcoWatch",
    layout="wide"
)


st.markdown(
    """
    <style>
    [data-testid="stStatusWidget"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    .stDeployButton {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.title("EcoWatch - Monitoramento Ambiental Urbano")
st.write("Dashboard com dados recebidos via MQTT e salvos no PostgreSQL/RDS.")


def carregar_dados(query):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def contar_leituras():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM leituras_ambientais;")
            return cursor.fetchone()[0]


# =========================
# SIDEBAR - RELATORIOS
# =========================

st.sidebar.subheader("Relatorios")

if "csv_bytes" not in st.session_state:
    st.session_state["csv_bytes"] = None
    st.session_state["csv_filename"] = None
    st.session_state["csv_s3_key"] = None

if st.sidebar.button("Gerar relatorio CSV e enviar ao S3", key="botao_gerar_csv"):
    caminho_arquivo, total, chave_s3 = exportar_leituras_csv(enviar_s3=True)

    st.session_state["csv_bytes"] = Path(caminho_arquivo).read_bytes()
    st.session_state["csv_filename"] = Path(caminho_arquivo).name
    st.session_state["csv_s3_key"] = chave_s3

    st.sidebar.success(f"Relatorio gerado com {total} leituras.")

    if chave_s3:
        st.sidebar.info(f"Enviado ao S3: {chave_s3}")
    else:
        st.sidebar.warning("Relatorio gerado apenas localmente.")

if st.session_state["csv_bytes"] is not None:
    st.sidebar.download_button(
        label="Baixar relatorio CSV",
        data=st.session_state["csv_bytes"],
        file_name=st.session_state["csv_filename"],
        mime="text/csv",
        key="botao_baixar_csv"
    )


# =========================
# CONSULTAS
# =========================

leituras = carregar_dados("""
    SELECT 
        l.id,
        e.codigo AS estacao,
        e.nome AS nome_estacao,
        b.nome AS bairro,
        e.latitude,
        e.longitude,
        l.temperatura,
        l.umidade,
        l.co2,
        l.pm25,
        l.pm10,
        l.ruido,
        l.iqa,
        l.classificacao_iqa,
        l.criado_em
    FROM leituras_ambientais l
    JOIN estacoes e ON e.id = l.estacao_id
    JOIN bairros b ON b.id = e.bairro_id
    ORDER BY l.criado_em DESC
    LIMIT 100;
""")

alertas = carregar_dados("""
    SELECT
        a.id,
        e.codigo AS estacao,
        b.nome AS bairro,
        a.tipo,
        a.mensagem,
        a.nivel,
        a.criado_em
    FROM alertas a
    JOIN estacoes e ON e.id = a.estacao_id
    JOIN bairros b ON b.id = e.bairro_id
    ORDER BY a.criado_em DESC
    LIMIT 50;
""")


# =========================
# DASHBOARD
# =========================

if leituras.empty:
    st.warning("Ainda nao ha leituras no banco.")
else:
    total_leituras = contar_leituras()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Leituras registradas", total_leituras)
    col2.metric("IQA medio", round(leituras["iqa"].mean(), 2))
    col3.metric("PM2.5 medio", round(leituras["pm25"].mean(), 2))
    col4.metric("CO2 medio", round(leituras["co2"].mean(), 2))

    st.subheader("Mapa das estacoes ambientais")

    mapa = (
        leituras.sort_values("criado_em")
        .groupby(["estacao", "bairro", "latitude", "longitude"], as_index=False)
        .last()
    )

    mapa_streamlit = mapa.rename(
        columns={
            "latitude": "lat",
            "longitude": "lon"
        }
    )

    st.map(
        mapa_streamlit,
        latitude="lat",
        longitude="lon",
        size=200
    )

    st.subheader("Leituras recentes")
    st.dataframe(leituras, width="stretch")

    st.subheader("Ranking por pior qualidade do ar")

    ranking = (
        leituras.groupby(["estacao", "bairro"])["iqa"]
        .mean()
        .reset_index()
        .sort_values(by="iqa", ascending=False)
    )

    st.dataframe(ranking, width="stretch")

    st.subheader("Historico de IQA")

    grafico = leituras.sort_values("criado_em")
    st.line_chart(grafico, x="criado_em", y="iqa")


st.subheader("Alertas recentes")

if alertas.empty:
    st.info("Nenhum alerta registrado ainda.")
else:
    st.dataframe(alertas, width="stretch")


# =========================
# SIDEBAR - ATUALIZACAO
# =========================

st.sidebar.subheader("Atualizacao")

atualizacao_automatica = st.sidebar.checkbox(
    "Atualizar automaticamente",
    value=True,
    key="atualizacao_automatica_checkbox"
)

intervalo = st.sidebar.slider(
    "Intervalo de atualizacao em segundos",
    min_value=3,
    max_value=30,
    value=5,
    key="intervalo_atualizacao_slider"
)

if st.sidebar.button("Atualizar agora", key="botao_atualizar_agora"):
    st.rerun()

if atualizacao_automatica:
    st_autorefresh(
        interval=intervalo * 1000,
        key="ecowatch_autorefresh"
    )