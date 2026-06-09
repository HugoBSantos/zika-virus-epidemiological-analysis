CREATE TABLE IF NOT EXISTS silver.ufs (
    uf_id SMALLINT PRIMARY KEY,
    sigla CHAR(2) NOT NULL UNIQUE,
    nome VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS silver.municipios (
    municipio_id INTEGER PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    uf_id SMALLINT NOT NULL REFERENCES silver.ufs(uf_id)
);

CREATE TABLE IF NOT EXISTS silver.paises (
    pais_id SMALLINT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS silver.regionais_saude (
    regional_id SMALLINT PRIMARY KEY,
    uf_id SMALLINT NOT NULL REFERENCES silver.ufs(uf_id)
);

CREATE TABLE IF NOT EXISTS silver.unidades_notificadoras (
    unidade_id INTEGER PRIMARY KEY,
    nome VARCHAR(50),
    tipo SMALLINT,
    municipio_id INTEGER NOT NULL REFERENCES silver.municipios(municipio_id)
);

CREATE TABLE IF NOT EXISTS silver.pacientes (
    paciente_id SERIAL PRIMARY KEY,
    idade_codificada SMALLINT NOT NULL,
    sexo VARCHAR(9) NOT NULL DEFAULT 'Ignorado',
    idade_gestacional VARCHAR(30) NOT NULL DEFAULT 'Ignorado',
    raca_cor VARCHAR(8) NOT NULL DEFAULT 'Ignorado',
    escolaridade VARCHAR(50) NOT NULL DEFAULT 'Ignorado',
    municipio_id INTEGER REFERENCES silver.municipios(municipio_id),
    regional_residencia SMALLINT REFERENCES silver.regionais_saude(regional_id),
    pais_id SMALLINT REFERENCES silver.paises(pais_id),
    ocupacao VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS silver.notificacoes_casos (
    notificacao_id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES silver.pacientes(paciente_id),
    data_notificacao DATE NOT NULL,
    semana_notificacao SMALLINT NOT NULL,
    unidade_id INTEGER REFERENCES silver.unidades_notificadoras(unidade_id),
    regional_notificacao SMALLINT REFERENCES silver.regionais_saude(regional_id),
    data_primeiros_sintomas DATE NOT NULL,
    semana_primeiros_sintomas SMALLINT NOT NULL,
    data_investigacao DATE,
    classificacao_final VARCHAR(20) NOT NULL,
    criterio_confirmacao VARCHAR(30),
    autoctonia VARCHAR(20) NOT NULL DEFAULT 'Indeterminado',
    uf_provavel_infeccao SMALLINT REFERENCES silver.ufs(uf_id),
    municipio_provavel_infeccao INTEGER REFERENCES silver.municipios(municipio_id),
    pais_provavel_infeccao SMALLINT REFERENCES silver.paises(pais_id),
    doenca_trabalho VARCHAR(10) NOT NULL DEFAULT 'Ignorado',
    evolucao_caso VARCHAR(30) NOT NULL DEFAULT 'Ignorado',
    -- NDUPLIC_N: flag do próprio SINAN; filtrar WHERE nduplic = FALSE em análises
    nduplic BOOLEAN NOT NULL DEFAULT FALSE,
    fluxo_retorno SMALLINT,
    fluxo_recebido SMALLINT
);

CREATE TABLE IF NOT EXISTS silver.obitos (
    obito_id SERIAL PRIMARY KEY,
    notificacao_id INTEGER NOT NULL REFERENCES silver.notificacoes_casos(notificacao_id),
    data_obito DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS silver.casos_encerrados (
    caso_encerrado_id SERIAL PRIMARY KEY,
    notificacao_id INTEGER NOT NULL REFERENCES silver.notificacoes_casos(notificacao_id),
    data_encerramento DATE NOT NULL
);
