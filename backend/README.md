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
backend/
├── app/
│   ├── main.py              # Entry point e montagem estática (/uploads)
│   ├── database.py          # Conexão PostgreSQL
│   ├── config.py            # Configurações (.env)
│   ├── models/              # Tabelas (SQLAlchemy ORM)
│   ├── schemas/             # Validação de dados (Pydantic)
│   ├── routers/             # Endpoints da API
│   └── auth/                # JWT e segurança
└── uploads/                 # Armazenamento físico de imagens em pastas por chamado
    └── chamados/
        └── {id_chamado}/    # Fotos vinculadas ao chamado
```

## Armazenamento de Imagens (Uploads e BI)

As fotos enviadas pelo sistema são salvas fisicamente no servidor em pastas separadas por chamado:
`uploads/chamados/{id_chamado}/{timestamp}_{uuid}_{nome_arquivo}`.

- **Para o BI:** O banco armazena em `chamado_fotos.caminho_foto` o caminho relativo exato para consumo e relatórios.
- **Para o Front-end:** As fotos são servidas automaticamente via rota estática em `http://localhost:8000/{caminho_foto}` (disponível no campo `url_foto` da API).

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Login (retorna JWT) |
| GET/POST | `/usuarios/` | Listar / Criar usuários |
| GET/POST | `/clientes/` | Listar / Criar clientes |
| GET/POST | `/tipos/` | Listar / Criar tipos de chamado |
| GET/POST | `/chamados/` | Listar / Abrir chamados |
| GET | `/chamados/dashboard` | Dados do dashboard |
| GET/POST | `/materiais/` | Listar / Cadastrar materiais (Lona, Telhas, Cesta, etc.) |
| GET/PUT/DELETE | `/materiais/{id}` | Consultar / Atualizar / Inativar material |
| GET/POST | `/chamados/{id}/materiais` | Listar / Vincular material e quantidade ao chamado |
| PUT/DELETE | `/chamados/{id}/materiais/{id_mat}` | Atualizar quantidade / Desvincular material |
| GET/POST | `/chamados/{id}/fotos` | Listar / Fazer upload de fotos (multipart/form-data) |
| DELETE | `/chamados/{id}/fotos/{id_foto}` | Excluir foto do banco e da pasta local |
