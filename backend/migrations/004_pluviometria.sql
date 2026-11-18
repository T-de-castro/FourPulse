-- 004_pluviometria.sql
CREATE TABLE IF NOT EXISTS pluviometria (
    id_medicao INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    estacao VARCHAR(100) NOT NULL DEFAULT 'INMET - Concórdia/Oeste SC',
    data_medicao DATE NOT NULL,
    hora VARCHAR(5),
    precipitacao_mm NUMERIC(6,2) NOT NULL DEFAULT 0.00,
    temperatura_c NUMERIC(4,1),
    umidade_pct NUMERIC(4,1),
    nivel_alerta VARCHAR(50) NOT NULL DEFAULT 'Normal',
    origem VARCHAR(100) NOT NULL DEFAULT 'INMET / Defesa Civil SC'
);

CREATE INDEX IF NOT EXISTS ix_pluviometria_data
    ON pluviometria (data_medicao DESC);
