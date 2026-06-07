CREATE TABLE IF NOT EXISTS bairros (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    uf CHAR(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS estacoes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    bairro_id INTEGER NOT NULL REFERENCES bairros(id),
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    status VARCHAR(20) DEFAULT 'ativa'
);

CREATE TABLE IF NOT EXISTS leituras_ambientais (
    id SERIAL PRIMARY KEY,
    estacao_id INTEGER NOT NULL REFERENCES estacoes(id),
    temperatura NUMERIC(5,2) NOT NULL,
    umidade NUMERIC(5,2) NOT NULL,
    co2 NUMERIC(8,2) NOT NULL,
    pm25 NUMERIC(8,2) NOT NULL,
    pm10 NUMERIC(8,2) NOT NULL,
    ruido NUMERIC(6,2) NOT NULL,
    iqa INTEGER,
    classificacao_iqa VARCHAR(50),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alertas (
    id SERIAL PRIMARY KEY,
    estacao_id INTEGER NOT NULL REFERENCES estacoes(id),
    tipo VARCHAR(50) NOT NULL,
    mensagem TEXT NOT NULL,
    nivel VARCHAR(20) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO bairros (nome, cidade, uf)
VALUES
('Nazare', 'Belem', 'PA'),
('Umarizal', 'Belem', 'PA'),
('Marco', 'Belem', 'PA')
ON CONFLICT DO NOTHING;

INSERT INTO estacoes (codigo, nome, bairro_id, latitude, longitude)
VALUES
('ECO-001', 'Estacao Nazare', 1, -1.455800, -48.490200),
('ECO-002', 'Estacao Umarizal', 2, -1.447600, -48.491900),
('ECO-003', 'Estacao Marco', 3, -1.434900, -48.457800)
ON CONFLICT (codigo) DO NOTHING;