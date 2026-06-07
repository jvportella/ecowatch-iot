import json
import os
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from database import get_connection


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "ecowatch/estacao/+/leituras"


def calcular_iqa_simples(pm25, pm10, co2, ruido):
    """
    IQA simplificado para fins academicos.
    Depois podemos explicar no relatorio que e uma classificacao demonstrativa.
    """
    if pm25 > 55 or pm10 > 120 or co2 > 1000 or ruido > 75:
        return 150, "Ruim"

    if pm25 > 35 or pm10 > 80 or co2 > 800 or ruido > 65:
        return 100, "Moderado"

    return 50, "Bom"


def gerar_alertas(estacao_id, dados):
    alertas = []

    if dados["pm25"] > 55:
        alertas.append(("PM2.5", "Nivel alto de particulas PM2.5", "alto"))

    if dados["pm10"] > 120:
        alertas.append(("PM10", "Nivel alto de particulas PM10", "alto"))

    if dados["co2"] > 1000:
        alertas.append(("CO2", "Nivel alto de CO2", "medio"))

    if dados["ruido"] > 75:
        alertas.append(("Ruido", "Nivel elevado de ruido ambiente", "medio"))

    return alertas


def salvar_leitura(dados):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM estacoes WHERE codigo = %s;",
                (dados["estacao_codigo"],)
            )

            resultado = cursor.fetchone()

            if resultado is None:
                print(f"Estacao nao encontrada: {dados['estacao_codigo']}")
                return

            estacao_id = resultado[0]

            iqa, classificacao = calcular_iqa_simples(
                dados["pm25"],
                dados["pm10"],
                dados["co2"],
                dados["ruido"]
            )

            cursor.execute(
                """
                INSERT INTO leituras_ambientais
                (
                    estacao_id,
                    temperatura,
                    umidade,
                    co2,
                    pm25,
                    pm10,
                    ruido,
                    iqa,
                    classificacao_iqa
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    estacao_id,
                    dados["temperatura"],
                    dados["umidade"],
                    dados["co2"],
                    dados["pm25"],
                    dados["pm10"],
                    dados["ruido"],
                    iqa,
                    classificacao
                )
            )

            for tipo, mensagem, nivel in gerar_alertas(estacao_id, dados):
                cursor.execute(
                    """
                    INSERT INTO alertas
                    (estacao_id, tipo, mensagem, nivel)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (estacao_id, tipo, mensagem, nivel)
                )

            conn.commit()

            print(
                f"Leitura salva | {dados['estacao_codigo']} | "
                f"IQA: {iqa} | Classificacao: {classificacao}"
            )


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Backend conectado ao broker MQTT.")
        client.subscribe(MQTT_TOPIC)
        print(f"Assinando topico: {MQTT_TOPIC}")
    else:
        print(f"Erro ao conectar no broker MQTT. Codigo: {rc}")


def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
        dados = json.loads(payload)

        print(f"Mensagem recebida em {message.topic}")
        salvar_leitura(dados)

    except Exception as erro:
        print("Erro ao processar mensagem MQTT:")
        print(erro)


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("Iniciando backend subscriber EcoWatch...")
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()