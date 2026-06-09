# EcoWatch IoT

Solução IoT end-to-end para monitoramento ambiental urbano usando **Python, MQTT, AWS EC2, RDS PostgreSQL, Amazon S3 e Streamlit**.

O projeto simula estações ambientais em bairros de Belém, envia leituras via MQTT para um broker na AWS, processa os dados em um backend, armazena as informações em um banco relacional privado e exibe os resultados em um dashboard web.

## Visão geral

O EcoWatch foi desenvolvido como projeto final de IoT com arquitetura em nuvem AWS. A solução cobre o fluxo completo:

```text
Simulador IoT
→ MQTT Broker na EC2
→ Backend Subscriber
→ RDS PostgreSQL
→ Dashboard Streamlit
→ Relatórios CSV/PDF no S3
```

## Funcionalidades

* Simulação de estações ambientais.
* Publicação de dados via MQTT.
* Broker Mosquitto hospedado em EC2.
* Backend subscriber em Python.
* Persistência em RDS PostgreSQL privado.
* Dashboard web com Streamlit.
* Mapa das estações.
* Ranking por pior qualidade do ar.
* Histórico de IQA.
* Alertas ambientais.
* Exportação de CSV histórico.
* Geração de relatório mensal em PDF.
* Envio de relatórios para Amazon S3.

## Dados simulados

Cada estação ambiental publica leituras com:

* Temperatura
* Umidade
* CO2
* PM2.5
* PM10
* Ruído ambiente

Estações simuladas:

| Código  | Bairro   |
| ------- | -------- |
| ECO-001 | Nazare   |
| ECO-002 | Umarizal |
| ECO-003 | Marco    |

## Arquitetura AWS

A infraestrutura foi criada no **AWS Academy Learner Lab**, na região `us-east-1`.

```text
AWS Cloud
└── VPC EcoWatch 10.0.0.0/16
    ├── Sub-rede pública 10.0.1.0/24
    │   └── EC2
    │       ├── Mosquitto Broker MQTT
    │       ├── Backend Subscriber Python
    │       └── Dashboard Streamlit
    │
    ├── Sub-rede privada A 10.0.2.0/24
    ├── Sub-rede privada B 10.0.3.0/24
    │   └── RDS PostgreSQL
    │
    └── S3
        ├── Relatórios CSV
        └── Relatórios PDF
```

A EC2 fica na sub-rede pública porque precisa receber conexões externas para SSH, MQTT e acesso ao dashboard. O RDS fica em sub-redes privadas e só aceita conexão vinda da EC2.

## Tecnologias utilizadas

| Camada         | Tecnologia                             |
| -------------- | -------------------------------------- |
| Simulador IoT  | Python, paho-mqtt                      |
| Broker MQTT    | Eclipse Mosquitto                      |
| Backend        | Python                                 |
| Banco de dados | Amazon RDS PostgreSQL                  |
| Dashboard      | Streamlit                              |
| Armazenamento  | Amazon S3                              |
| Infraestrutura | AWS VPC, EC2, RDS, S3, Security Groups |

## Estrutura do projeto

```text
ecowatch-iot/
├── backend/
│   ├── database.py
│   ├── mqtt_subscriber.py
│   ├── export_reports.py
│   └── test_db.py
│
├── dashboard/
│   └── app.py
│
├── database/
│   └── schema.sql
│
├── simulator/
│   └── sensor_simulator.py
│
├── storage/
│   └── exports/
│
├── .env.example
├── requirements.txt
└── README.md
```

## Banco de dados

O banco PostgreSQL possui as seguintes tabelas principais:

| Tabela                | Função                                  |
| --------------------- | --------------------------------------- |
| `bairros`             | Armazena os bairros monitorados         |
| `estacoes`            | Armazena as estações ambientais         |
| `leituras_ambientais` | Armazena as leituras recebidas via MQTT |
| `alertas`             | Armazena alertas gerados pelo backend   |

Relacionamentos principais:

```text
bairros 1:N estacoes
estacoes 1:N leituras_ambientais
estacoes 1:N alertas
```

## IQA simplificado

O projeto utiliza um IQA simplificado para fins acadêmicos:

| Valor | Classificação |
| ----- | ------------- |
| 50    | Bom           |
| 100   | Moderado      |
| 150   | Ruim          |

A classificação considera limites definidos para PM2.5, PM10, CO2 e ruído. O objetivo é demonstrar processamento dos dados ambientais e geração de alertas, não substituir índices oficiais de órgãos ambientais.

## Variáveis de ambiente

Crie um arquivo `.env` baseado no `.env.example`:

```env
MQTT_HOST=localhost
MQTT_PORT=1883

DB_HOST=endpoint-do-rds
DB_PORT=5432
DB_NAME=ecowatch_db
DB_USER=postgres
DB_PASSWORD=sua_senha

AWS_REGION=us-east-1
S3_BUCKET=nome-do-bucket
```

O arquivo `.env` não deve ser enviado ao GitHub.

## Como executar

### 1. Clonar o projeto

```powershell
git clone https://github.com/jvportela04/ecowatch-iot.git
cd ecowatch-iot
```

### 2. Criar ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Rodar o backend subscriber na EC2

```bash
cd ~/ecowatch-iot
source .venv/bin/activate
python backend/mqtt_subscriber.py
```

### 4. Rodar o dashboard na EC2

```bash
cd ~/ecowatch-iot
source .venv/bin/activate
python -m streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501
```

Acesse no navegador:

```text
http://IP_PUBLICO_EC2:8501
```

### 5. Rodar o simulador no notebook

```powershell
cd "$HOME\Documents\ecowatch-iot"
.\.venv\Scripts\activate
$env:MQTT_HOST="IP_PUBLICO_EC2"
$env:MQTT_PORT="1883"
python .\simulator\sensor_simulator.py
```

## Relatórios

O dashboard permite gerar:

* CSV histórico com as leituras ambientais.
* PDF mensal com resumo, médias, ranking e classificações de IQA.

Os arquivos são enviados para o S3 nas pastas:

```text
relatorios/
relatorios_pdf/
```

Também é possível gerar os relatórios via script:

```bash
python -u backend/export_reports.py
```

## Segurança

A arquitetura utiliza Security Groups separados:

| Security Group    | Função                                  |
| ----------------- | --------------------------------------- |
| `ecowatch-ec2-sg` | Libera SSH, MQTT e dashboard para a EC2 |
| `ecowatch-rds-sg` | Libera PostgreSQL apenas para a EC2     |

O RDS não possui acesso público. Apenas a EC2 pode se conectar ao banco pela porta `5432`.

## Aderência ao projeto

O EcoWatch atende aos principais requisitos do projeto IoT em nuvem:

* VPC dedicada.
* Sub-rede pública para EC2.
* Sub-redes privadas para RDS.
* Internet Gateway e tabela de rotas pública.
* Security Groups segmentados.
* EC2 atuando como broker MQTT.
* Backend subscriber processando mensagens.
* RDS PostgreSQL privado.
* S3 para relatórios CSV e PDF.
* Simulador IoT publicando dados periodicamente.
* Dashboard exibindo dados atualizados.
* Repositório com código, SQL e documentação.

## Status

Projeto funcional e validado em ambiente AWS Academy Learner Lab.

Fluxo validado:

```text
Simulador → MQTT → Backend → RDS → Dashboard → S3
```
