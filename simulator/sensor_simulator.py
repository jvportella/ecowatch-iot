import json
import os
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt
from dotenv import load_dotenv


load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

ESTACOES = [
    {"codigo": "ECO-001", "bairro": "Nazare"},
    {"codigo": "ECO-002", "bairro": "Umarizal"},
    {"codigo": "ECO-003", "bairro": "Marco"},
]


def gerar_leitura(estacao):
    return {
        "estacao_codigo": estacao["codigo"],
        "bairro": estacao["bairro"],
        "temperatura": round(random.uniform(25, 35), 2),
        "umidade": round(random.uniform(55, 90), 2),
        "co2": round(random.uniform(400, 1200), 2),
        "pm25": round(random.uniform(5, 80), 2),
        "pm10": round(random.uniform(10, 150), 2),
        "ruido": round(random.uniform(40, 90), 2),
        "timestamp": datetime.now().isoformat()
    }


def main():
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    print("Simulador EcoWatch iniciado.")
    print("Publicando leituras MQTT...")

    while True:
        for estacao in ESTACOES:
            leitura = gerar_leitura(estacao)
            topico = f"ecowatch/estacao/{estacao['codigo']}/leituras"

            client.publish(topico, json.dumps(leitura))
            print(f"Publicado em {topico}: {leitura}")

        time.sleep(5)


if __name__ == "__main__":
    main()