-- ============================================
-- 360ti API - Database Schema
-- ============================================

CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE OR REPLACE FUNCTION public.unaccent_immutable(text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT unaccent($1);
$$;

-- ============================================
-- CLIENTES (API Key Auth)
-- ============================================
CREATE TABLE IF NOT EXISTS clientes_api (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) NOT NULL UNIQUE,
    ativo INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_clientes_api_api_key ON clientes_api (api_key);

-- Chave padrão de desenvolvimento — troque em produção!
INSERT INTO clientes_api (nome, api_key, ativo)
VALUES ('admin', 'changeme-dev-key', 1)
ON CONFLICT (api_key) DO NOTHING;

-- ============================================
-- PAÍSES
-- ============================================
CREATE TABLE IF NOT EXISTS ibge_paises (
    codigo SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    sigla VARCHAR(3),
    origem INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    excluido_em TIMESTAMP
);

ALTER TABLE ibge_paises
ADD COLUMN IF NOT EXISTS nome_busca text
GENERATED ALWAYS AS (lower(unaccent_immutable(nome))) STORED;

CREATE INDEX IF NOT EXISTS idx_ibge_paises_nome_busca_trgm
ON ibge_paises USING gin (nome_busca gin_trgm_ops);

-- ============================================
-- ESTADOS
-- ============================================
CREATE TABLE IF NOT EXISTS ibge_estados (
    codigo SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    sigla VARCHAR(2),
    pais_codigo INTEGER NOT NULL REFERENCES ibge_paises(codigo) ON DELETE CASCADE,
    origem INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    excluido_em TIMESTAMP
);

ALTER TABLE ibge_estados
ADD COLUMN IF NOT EXISTS nome_busca text
GENERATED ALWAYS AS (lower(unaccent_immutable(nome))) STORED;

CREATE INDEX IF NOT EXISTS idx_ibge_estados_nome_busca_trgm
ON ibge_estados USING gin (nome_busca gin_trgm_ops);

-- ============================================
-- CIDADES
-- ============================================
CREATE TABLE IF NOT EXISTS ibge_cidades (
    codigo SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    estado_codigo INTEGER NOT NULL REFERENCES ibge_estados(codigo) ON DELETE CASCADE,
    codigocorreios INTEGER,
    origem INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    excluido_em TIMESTAMP
);

ALTER TABLE ibge_cidades
ADD COLUMN IF NOT EXISTS nome_busca text
GENERATED ALWAYS AS (lower(unaccent_immutable(nome))) STORED;

CREATE INDEX IF NOT EXISTS idx_ibge_cidades_nome_busca_trgm
ON ibge_cidades USING gin (nome_busca gin_trgm_ops);

-- ============================================
-- TIPOS DE LOGRADOURO
-- ============================================
CREATE TABLE IF NOT EXISTS tipos_logradouros (
    codigo SERIAL PRIMARY KEY,
    nome VARCHAR(255),
    sigla VARCHAR(50),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    excluido_em TIMESTAMP
);

-- ============================================
-- CEPS
-- ============================================
CREATE TABLE IF NOT EXISTS correios_ceps (
    cep VARCHAR(9) PRIMARY KEY,
    tipo_logradouro_codigo INTEGER REFERENCES tipos_logradouros(codigo) ON DELETE CASCADE,
    logradouro VARCHAR(255),
    numero INTEGER,
    complemento VARCHAR(255),
    bairro VARCHAR(255),
    cidade_codigo INTEGER REFERENCES ibge_cidades(codigo) ON DELETE CASCADE,
    uf_codigo INTEGER REFERENCES ibge_estados(codigo) ON DELETE CASCADE,
    pais_codigo INTEGER REFERENCES ibge_paises(codigo) ON DELETE CASCADE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    excluido_em TIMESTAMP
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_correios_ceps_cep_prefix
ON correios_ceps (cep text_pattern_ops);

ALTER TABLE correios_ceps
ADD COLUMN IF NOT EXISTS logradouro_busca text
GENERATED ALWAYS AS (lower(unaccent_immutable(logradouro))) STORED;

CREATE INDEX IF NOT EXISTS idx_correios_ceps_logradouro_trgm
ON correios_ceps USING gin (logradouro_busca gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_correios_ceps_cep_numeric_prefix
ON correios_ceps (regexp_replace(cep, '[^0-9]', '', 'g') text_pattern_ops);
