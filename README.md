# EcoWatch IoT

Projeto IoT End-to-End para monitoramento ambiental urbano, desenvolvido para simular estações de qualidade do ar enviando dados via MQTT, com persistência em PostgreSQL e visualização em dashboard.

## Objetivo

O EcoWatch monitora dados ambientais de estações simuladas em bairros de Belém. O sistema coleta informações como temperatura, umidade, CO2, PM2.5, PM10 e ruído ambiente, classifica a qualidade do ar por meio de um IQA simplificado e gera alertas quando os valores ultrapassam limites definidos.

## Arquitetura local

O fluxo local do projeto é:

```text
Simulador IoT em Python
→ Broker MQTT Mosquitto
→ Backend Subscriber em Python
→ Banco PostgreSQL
→ Dashboard Streamlit
→ Exportação CSV