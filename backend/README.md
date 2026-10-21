# Backend — FourPulse

API REST em Python/FastAPI para o sistema de Controle de Chamados da Defesa Civil.

## Pré-requisitos

- Python 3.10+
- PostgreSQL instalado e rodando

## Configuração

```bash
# 1. Entre na pasta do backend
cd backend

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com seus dados do PostgreSQL

# 5. Crie o banco de dados no PostgreSQL
psql -U postgres -c "CREATE DATABASE fourpulse;"
```

## Rodando

```bash
uvicorn app.main:app --reload
```

A API estará disponível em: http://localhost:8000

Documentação interativa: http://localhost:8000/docs

## Estrutura

```
app/
├── main.py              # Entry point
├── database.py          # Conexão PostgreSQL
├── config.py            # Configurações (.env)
├── models/              # Tabelas (SQLAlchemy ORM)
├── schemas/             # Validação de dados (Pydantic)
├── routers/             # Endpoints da API
└── auth/                # JWT e segurança
```

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /auth/login | Login (retorna JWT) |
| GET/POST | /usuarios/ | Listar / Criar usuários |
| GET/POST | /cidadaos/ | Listar / Criar cidadãos |
| GET/POST | /tipos/ | Listar / Criar tipos de ocorrência |
| GET/POST | /chamados/ | Listar / Abrir chamados |
| GET | /chamados/dashboard | Dados do dashboard |
