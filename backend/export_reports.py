import os
from datetime import datetime
from pathlib import Path

import boto3
import pandas as pd
from dotenv import load_dotenv

from database import get_connection


BASE_DIR = Path(__file__).resolve().parents[1]
EXPORT_DIR = BASE_DIR / "storage" / "exports"

load_dotenv(BASE_DIR / ".env")


def enviar_para_s3(caminho_arquivo):
    bucket = os.getenv("S3_BUCKET")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not bucket:
        return None

    chave_s3 = f"relatorios/{caminho_arquivo.name}"

    s3 = boto3.client("s3", region_name=region)
    s3.upload_file(str(caminho_arquivo), bucket, chave_s3)

    return chave_s3


def exportar_leituras_csv(enviar_s3=False):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

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
        df = pd.read_sql_query(query, conn)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_arquivo = EXPORT_DIR / f"relatorio_leituras_{timestamp}.csv"

    df.to_csv(caminho_arquivo, index=False, encoding="utf-8-sig")

    chave_s3 = None

    if enviar_s3:
        chave_s3 = enviar_para_s3(caminho_arquivo)

    return caminho_arquivo, len(df), chave_s3


if __name__ == "__main__":
    caminho, total, chave_s3 = exportar_leituras_csv(enviar_s3=True)

    print(f"Relatorio gerado com sucesso: {caminho}")
    print(f"Total de leituras exportadas: {total}")

    if chave_s3:
        print(f"Relatorio enviado ao S3: {chave_s3}")
    else:
        print("Relatorio gerado apenas localmente.")