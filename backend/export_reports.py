from datetime import datetime
from pathlib import Path

import pandas as pd

from database import get_connection


BASE_DIR = Path(__file__).resolve().parents[1]
EXPORT_DIR = BASE_DIR / "storage" / "exports"


def exportar_leituras_csv():
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

    return caminho_arquivo, len(df)


if __name__ == "__main__":
    caminho, total = exportar_leituras_csv()
    print(f"Relatorio gerado com sucesso: {caminho}")
    print(f"Total de leituras exportadas: {total}")