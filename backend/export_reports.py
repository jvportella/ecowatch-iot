import os
from datetime import datetime
from pathlib import Path

import boto3
import pandas as pd
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet

from database import get_connection


BASE_DIR = Path(__file__).resolve().parents[1]
EXPORT_DIR = BASE_DIR / "storage" / "exports"

load_dotenv(BASE_DIR / ".env")


def enviar_para_s3(caminho_arquivo, pasta_s3="relatorios"):
    bucket = os.getenv("S3_BUCKET")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not bucket:
        return None

    chave_s3 = f"{pasta_s3}/{caminho_arquivo.name}"

    s3 = boto3.client("s3", region_name=region)
    s3.upload_file(str(caminho_arquivo), bucket, chave_s3)

    return chave_s3


def carregar_leituras():
    query = """
        SELECT 
            l.id,
            e.codigo AS estacao,
            e.nome AS nome_estacao,
            b.nome AS bairro,
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
        ORDER BY l.criado_em DESC;
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def exportar_leituras_csv(enviar_s3=False):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = carregar_leituras()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_arquivo = EXPORT_DIR / f"relatorio_leituras_{timestamp}.csv"

    df.to_csv(caminho_arquivo, index=False, encoding="utf-8-sig")

    chave_s3 = None

    if enviar_s3:
        chave_s3 = enviar_para_s3(caminho_arquivo, pasta_s3="relatorios")

    return caminho_arquivo, len(df), chave_s3


def exportar_relatorio_mensal_pdf(enviar_s3=False):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = carregar_leituras()

    agora = datetime.now()
    ano = agora.year
    mes = agora.month

    df["criado_em"] = pd.to_datetime(df["criado_em"])
    df_mes = df[
        (df["criado_em"].dt.year == ano) &
        (df["criado_em"].dt.month == mes)
    ]

    timestamp = agora.strftime("%Y%m%d_%H%M%S")
    caminho_pdf = EXPORT_DIR / f"relatorio_mensal_ecowatch_{ano}_{mes:02d}_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        str(caminho_pdf),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()
    elementos = []

    titulo = Paragraph("Relatorio Mensal EcoWatch", styles["Title"])
    subtitulo = Paragraph(f"Periodo: {mes:02d}/{ano}", styles["Heading2"])

    elementos.append(titulo)
    elementos.append(subtitulo)
    elementos.append(Spacer(1, 12))

    if df_mes.empty:
        elementos.append(Paragraph("Nao ha leituras registradas para este mes.", styles["Normal"]))
    else:
        total_leituras = len(df_mes)
        total_estacoes = df_mes["estacao"].nunique()
        iqa_medio = round(df_mes["iqa"].mean(), 2)
        pm25_medio = round(df_mes["pm25"].mean(), 2)
        pm10_medio = round(df_mes["pm10"].mean(), 2)
        co2_medio = round(df_mes["co2"].mean(), 2)
        ruido_medio = round(df_mes["ruido"].mean(), 2)

        resumo = [
            ["Indicador", "Valor"],
            ["Total de leituras", total_leituras],
            ["Estacoes monitoradas", total_estacoes],
            ["IQA medio", iqa_medio],
            ["PM2.5 medio", pm25_medio],
            ["PM10 medio", pm10_medio],
            ["CO2 medio", co2_medio],
            ["Ruido medio", ruido_medio],
        ]

        tabela_resumo = Table(resumo, colWidths=[8 * cm, 6 * cm])
        tabela_resumo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ]))

        elementos.append(Paragraph("Resumo geral", styles["Heading2"]))
        elementos.append(tabela_resumo)
        elementos.append(Spacer(1, 16))

        ranking = (
            df_mes.groupby(["estacao", "bairro"])["iqa"]
            .mean()
            .reset_index()
            .sort_values(by="iqa", ascending=False)
        )

        dados_ranking = [["Estacao", "Bairro", "IQA medio"]]

        for _, linha in ranking.iterrows():
            dados_ranking.append([
                linha["estacao"],
                linha["bairro"],
                round(linha["iqa"], 2)
            ])

        tabela_ranking = Table(dados_ranking, colWidths=[4 * cm, 5 * cm, 4 * cm])
        tabela_ranking.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ]))

        elementos.append(Paragraph("Ranking mensal por pior qualidade do ar", styles["Heading2"]))
        elementos.append(tabela_ranking)
        elementos.append(Spacer(1, 16))

        classificacoes = (
            df_mes["classificacao_iqa"]
            .value_counts()
            .reset_index()
        )

        classificacoes.columns = ["Classificacao", "Quantidade"]

        dados_classificacao = [["Classificacao", "Quantidade"]]

        for _, linha in classificacoes.iterrows():
            dados_classificacao.append([
                linha["Classificacao"],
                int(linha["Quantidade"])
            ])

        tabela_classificacao = Table(dados_classificacao, colWidths=[8 * cm, 5 * cm])
        tabela_classificacao.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ]))

        elementos.append(Paragraph("Distribuicao das classificacoes de IQA", styles["Heading2"]))
        elementos.append(tabela_classificacao)
        elementos.append(Spacer(1, 16))

        texto_final = (
            "Este relatorio foi gerado automaticamente a partir das leituras ambientais "
            "armazenadas no banco RDS PostgreSQL. Os dados foram coletados por estacoes "
            "simuladas, enviados por MQTT, processados pelo backend e persistidos em nuvem."
        )

        elementos.append(Paragraph(texto_final, styles["Normal"]))

    doc.build(elementos)

    chave_s3 = None

    if enviar_s3:
        chave_s3 = enviar_para_s3(caminho_pdf, pasta_s3="relatorios_pdf")

    return caminho_pdf, len(df_mes), chave_s3


if __name__ == "__main__":
    caminho_csv, total_csv, chave_csv = exportar_leituras_csv(enviar_s3=True)
    print(f"CSV gerado: {caminho_csv}")
    print(f"Total de leituras exportadas: {total_csv}")
    print(f"CSV enviado ao S3: {chave_csv}")

    caminho_pdf, total_pdf, chave_pdf = exportar_relatorio_mensal_pdf(enviar_s3=True)
    print(f"PDF gerado: {caminho_pdf}")
    print(f"Total de leituras no PDF mensal: {total_pdf}")
    print(f"PDF enviado ao S3: {chave_pdf}")