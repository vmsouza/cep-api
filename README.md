# CEP API — Base de CEP Centralizada

Uma única base de dados de CEP, cidades, estados e países, consumida por **múltiplos sistemas** através de chaves de API individuais.

Em vez de cada sistema manter sua própria cópia da tabela de CEP (com mais de 1,2 milhão de registros), todos compartilham a mesma base centralizada. Cada cliente recebe uma chave única que pode ser **ativada, desativada ou revogada** a qualquer momento — sem precisar redeploy ou alteração nos sistemas consumidores.

🔗 **Repositório:** [github.com/vmsouza/cep-api](https://github.com/vmsouza/cep-api)

## Como funciona

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Sistema A   │   │ Sistema B   │   │ Sistema C   │
│ (chave abc) │   │ (chave xyz) │   │ (chave 123) │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │ X-API-Key
                         ▼
                ┌─────────────────┐
                │   CEP API      │
                │  (FastAPI/Python)│
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   PostgreSQL    │
                │ 1,2M CEPs      │
                │ 11k cidades    │
                │ 27 estados     │
                │ 254 países     │
                └─────────────────┘
```

Cada sistema se autentica com seu próprio `X-API-Key`. As chaves são cadastradas na tabela `clientes_api` e podem ser **ativadas, desativadas ou revogadas** em tempo real — sem afetar os demais clientes.

## Tecnologias

- **Python 3.12** + **FastAPI** (assíncrono)
- **PostgreSQL 16** com índices trigram para busca textual
- **SQLAlchemy 2.0** (async) + asyncpg
- **Autenticação**: API Key via header `X-API-Key`
- **Docker** com rede isolada /28

## Sumário

- [Instalação](#instalação)
- [Endpoints](#endpoints)
- [Exemplos de uso](#exemplos-de-uso)
- [Gerenciar chaves de API](#gerenciar-chaves-de-api)
- [Portas](#portas)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Licença](#licença)

---

## Instalação

### Pré-requisitos

- Docker e Docker Compose
- Python 3.12+ (para o script de seed)
- curl (para testar)

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/vmsouza/cep-api.git
cd cep-api

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite as senhas e portas se necessário

# 3. Inicie os containers
docker compose up -d --build

# 4. Baixe os dados públicos de CEP, cidades, estados e países
./download_data.sh

# 5. Popule o banco de dados
python3 seed_data.py

# 6. Teste
curl -H "X-API-Key: changeme-dev-key" \
  http://localhost:11050/api/cep/92030210
```

> **Dica:** Se já tiver os dados em outro diretório:
> ```bash
> DATA_DIR=/caminho/para/seu/data python3 seed_data.py
> ```

### Usando sem Docker (desenvolvimento)

```bash
# Instale as dependências
pip install -r requirements.txt

# Configure o banco PostgreSQL manualmente e aponte as env vars
DB_HOST=localhost DB_PORT=5432 DB_NAME=cep-api DB_USER=cep-api DB_PASS=changeme \
python3 seed_data.py

# Inicie o servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Endpoints

### CEP

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/cep/search` | Busca por prefixo de CEP ou nome do logradouro |
| `GET`  | `/api/cep/{cep}` | Busca exata por CEP (com ou sem traço) |

Parâmetros da busca (`POST`):

| Campo | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `q` | string | — | Termo de busca (mín. 3 caracteres) |
| `limit` | int | 30 | Máximo de resultados |

### Cidades

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/cidades/search` | Busca cidades por nome |
| `GET`  | `/api/cidades/{codigo}` | Retorna cidade pelo código IBGE |

### Estados

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET`  | `/api/estados` | Lista todos os estados |
| `GET`  | `/api/estados/{codigo}` | Retorna estado pelo código |

### Países

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET`  | `/api/paises` | Lista todos os países |
| `GET`  | `/api/paises/{codigo}` | Retorna país pelo código |

### Health

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET`  | `/api/health` | Health check (público, sem auth) |

---

## Exemplos de uso

```bash
# Variável para facilitar
KEY="changeme-dev-key"
API="http://localhost:11050"

# --- CEP ---

# Busca exata
curl -H "X-API-Key: $KEY" "$API/api/cep/92030210"

# Busca exata com traço
curl -H "X-API-Key: $KEY" "$API/api/cep/92030-210"

# Busca por prefixo numérico
curl -H "X-API-Key: $KEY" -X POST "$API/api/cep/search" \
  -H "Content-Type: application/json" \
  -d '{"q": "01310"}'

# Busca por nome de logradouro
curl -H "X-API-Key: $KEY" -X POST "$API/api/cep/search" \
  -H "Content-Type: application/json" \
  -d '{"q": "paulista", "limit": 5}'

# --- CIDADES ---

# Busca por nome
curl -H "X-API-Key: $KEY" -X POST "$API/api/cidades/search" \
  -H "Content-Type: application/json" \
  -d '{"q": "canoas"}'

# Busca com limite
curl -H "X-API-Key: $KEY" -X POST "$API/api/cidades/search" \
  -H "Content-Type: application/json" \
  -d '{"q": "sao paulo", "limit": 5}'

# Cidade por código IBGE
curl -H "X-API-Key: $KEY" "$API/api/cidades/3550308"

# --- ESTADOS ---

# Listar todos
curl -H "X-API-Key: $KEY" "$API/api/estados"

# Estado por código
curl -H "X-API-Key: $KEY" "$API/api/estados/35"

# --- PAÍSES ---

# Listar todos
curl -H "X-API-Key: $KEY" "$API/api/paises"

# País por código
curl -H "X-API-Key: $KEY" "$API/api/paises/55"

# --- HEALTH (público) ---
curl "$API/api/health"
```

### Exemplo de resposta (CEP)

```json
{
  "data": [
    {
      "cep": "01310-000",
      "logradouro": "Avenida Paulista",
      "bairro": "Bela Vista",
      "cidade_codigo": 3550308,
      "cidade": "São Paulo",
      "uf": "SP",
      "display": "01310-000 - Avenida Paulista - Bela Vista - São Paulo - SP"
    }
  ]
}
```

### Exemplo de resposta (cidades)

```json
{
  "code": "0",
  "data": [
    {
      "codigo": 4304606,
      "nome": "Canoas",
      "estado": {
        "sigla": "RS",
        "nome": "Rio Grande do Sul"
      },
      "display": "Canoas / RS"
    }
  ]
}
```

---

## Gerenciar chaves de API (clientes)

Cada sistema ou cliente que consome a API precisa de uma chave própria na tabela `clientes_api`. O acesso é controlado individualmente: é possível **ativar, desativar ou revogar** sem afetar os demais.

Conecte no banco PostgreSQL para gerenciar:

```bash
# Acessar o banco
psql -h localhost -p 11055 -U cep-api -d cep-api
# Senha: changeme
```

### Adicionar nova chave

```sql
INSERT INTO clientes_api (nome, api_key, ativo)
VALUES ('Nome do Cliente', 'chave-super-segura-123', 1);
```

### Listar todas as chaves

```sql
SELECT id, nome, api_key, ativo FROM clientes_api;
```

### Desativar uma chave (suspender acesso)

```sql
UPDATE clientes_api SET ativo = 0 WHERE api_key = 'chave-super-segura-123';
```

### Reativar uma chave

```sql
UPDATE clientes_api SET ativo = 1 WHERE api_key = 'chave-super-segura-123';
```

### Revogar (remover) uma chave

```sql
DELETE FROM clientes_api WHERE api_key = 'chave-super-segura-123';
```
> Use DELETE com cuidado — o cliente perderá acesso imediatamente.

### Gerar chave segura

```bash
# Linux/Mac
openssl rand -hex 32

# Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Portas

| Serviço | Interna (container) | Externa (host) | Configurável via |
|---------|---------------------|----------------|------------------|
| API     | 8000                | 11050          | `API_PORT` no `.env` |
| PostgreSQL | 5432             | 11055          | `DB_PORT` no `.env`  |

---

## Estrutura do projeto

```
cep-api/
├── app/
│   ├── main.py              # Entrada da aplicação FastAPI
│   ├── config.py            # Configurações via variáveis de ambiente
│   ├── database.py          # Engine e sessão assíncrona (SQLAlchemy)
│   ├── models/
│   │   └── models.py        # Modelos: IbgePaises, IbgeEstados, IbgeCidades,
│   │                        #            CorreiosCeps, TiposLogradouros, ClienteApi
│   ├── schemas/
│   │   └── schemas.py       # Schemas Pydantic (request/response)
│   ├── routers/
│   │   ├── cep.py           # Endpoints de CEP
│   │   ├── cidades.py       # Endpoints de cidades
│   │   ├── estados.py       # Endpoints de estados
│   │   └── paises.py        # Endpoints de países
│   └── middleware/
│       └── api_key.py       # Middleware de autenticação via X-API-Key
├── db/
│   └── init.sql             # Schema SQL executado na primeira inicialização
├── docker-compose.yml       # Orquestração dos containers
├── Dockerfile               # Imagem da API
├── download_data.sh         # Script para baixar dados públicos
├── seed_data.py             # Script para popular o banco
├── requirements.txt         # Dependências Python
├── .env.example             # Exemplo de configuração
└── LICENSE                  # Licença MIT
```

---

## Variáveis de ambiente

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `APP_NAME` | não | `CEP API` | Nome da aplicação |
| `APP_VERSION` | não | `1.0.0` | Versão |
| `DEBUG` | não | `false` | Modo debug (echo SQL) |
| `DB_USER` | não | `cep-api` | Usuário do PostgreSQL |
| `DB_PASS` | **sim** | `changeme` | Senha do PostgreSQL |
| `DB_NAME` | não | `cep-api` | Nome do banco |
| `API_PORT` | não | `11050` | Porta externa da API |
| `DB_PORT` | não | `11055` | Porta externa do PostgreSQL |

---

## Licença

MIT — veja o arquivo [LICENSE](LICENSE).
