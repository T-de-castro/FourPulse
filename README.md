# FourPulse — Defesa Civil

Sistema de atendimento e controle de chamados da Defesa Civil de Concórdia. O projeto tem uma API REST em FastAPI, uma interface em Streamlit e PostgreSQL como banco de dados. O painel Power BI fica em `BI/`.

## Integração

- O Streamlit consulta e altera os registros da API; os dados exibidos vêm do PostgreSQL, sem registros fictícios ou persistência temporária no frontend.
- A equipe entra com usuários cadastrados na tabela `usuarios`.
- Clientes podem criar uma conta pela tela inicial. As credenciais ficam na tabela `cliente_contas`, separada dos campos de cadastro do cliente. Cada cliente consulta apenas seus chamados e pode abrir chamados com fotos.
- As imagens ficam em `Backend/uploads/` e são servidas pela API.
- O frontend usa `http://localhost:8000` por padrão. Configure `FOURPULSE_API_URL` se a API estiver em outro endereço.
- O backend usa `CIDADE_PADRAO` e `ESTADO_PADRAO` como localidade de cadastro para contas de cliente. O cadastro interno usa `FOURPULSE_CIDADE` para a cidade padrão.

## Pré-requisitos

- Python 3.10 ou superior
- PostgreSQL instalado e em execução
- `psql` disponível no terminal (para preparar o banco)

## Preparar o banco de dados

O banco FourPulse existente foi identificado como `PulseDesk`, na instalação PostgreSQL 17 (porta 5433). Para ele, aplique a migração aditiva no PowerShell:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5433 -U SEU_USUARIO -d PulseDesk -f .\Backend\migrations\001_cliente_auth.sql
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5433 -U SEU_USUARIO -d PulseDesk -f .\Backend\migrations\002_telefone_canal_chamado.sql
```

O `psql` solicitará a senha do usuário do PostgreSQL. As migrações criam a tabela de credenciais de clientes, adicionam os campos que faltarem e habilitam o canal Telefone; podem ser executadas mais de uma vez. Para uma instalação diferente, ajuste executável, porta e nome do banco. Para criar um banco novo, use `Arquitetura/banco.sql` após criar o banco.

## Iniciar o backend

Abra um PowerShell na pasta do projeto:

```powershell
cd .\Backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Use `python` (não `py`): neste computador o launcher `py` aponta para uma instalação Python 3.14 inexistente, enquanto `python` seleciona o Python 3.13 instalado. Não é necessário ativar o ambiente virtual, evitando também bloqueios da política de execução do PowerShell.

Edite `Backend/.env` e informe a conexão do banco `PulseDesk` na instalação PostgreSQL 17, incluindo o usuário e a senha usados para conectar ao banco. Codifique na URL caracteres especiais da senha (`@` vira `%40`, por exemplo). Gere uma chave JWT com `python -c "import secrets; print(secrets.token_urlsafe(32))"` e substitua o valor de exemplo:

```dotenv
DATABASE_URL=postgresql+psycopg2://SEU_USUARIO:SUA_SENHA@localhost:5433/PulseDesk
SECRET_KEY=CHAVE_ALEATORIA_DE_PELO_MENOS_32_CARACTERES
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CIDADE_PADRAO=Concórdia
ESTADO_PADRAO=SC
CORS_ORIGINS=["http://localhost:8501","http://127.0.0.1:8501"]
```

O backend rejeita a chave secreta de exemplo e chaves menores que 32 caracteres. Para API fora da máquina local, configure HTTPS e atualize `CORS_ORIGINS` com as origens confiáveis.

Crie uma conta de administrador de teste (a senha é gerada aleatoriamente, armazenada com hash e exibida uma única vez):

```powershell
.\.venv\Scripts\python.exe .\create_admin.py --test-account
```

Anote o e-mail e a senha impressos. Para cadastrar um administrador com seus próprios dados em vez da conta de teste:

```powershell
.\.venv\Scripts\python.exe .\create_admin.py
```

Inicie a API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- API: <http://localhost:8000>
- Documentação interativa: <http://localhost:8000/docs>

## Iniciar o frontend

Abra **outro** PowerShell na pasta do projeto:

```powershell
cd .\Frontend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:FOURPULSE_API_URL = "http://localhost:8000"
$env:FOURPULSE_CIDADE = "Concórdia"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

O Streamlit abrirá em <http://localhost:8501>. Mantenha os dois terminais abertos: a API e o PostgreSQL precisam estar ativos para usar a interface.

## Principais rotas

| Grupo | Rotas | Uso |
|---|---|---|
| Autenticação da equipe | `POST /auth/login` | Login com usuário e senha |
| Contas de clientes | `POST /clientes/conta/registrar`, `POST /clientes/conta/login`, `GET /clientes/conta/me` | Cadastro, login e perfil |
| Clientes | `/clientes/` | Consultar e cadastrar clientes (autenticado) |
| Tipos | `/tipos/` | Consultar e cadastrar tipos |
| Materiais | `/materiais/` | Consultar e cadastrar materiais |
| Chamados da equipe | `/chamados/`, `/chamados/{id}`, `/chamados/{id}/materiais/lote` | Consultar, abrir e atualizar chamados e registrar vários materiais em lote |
| Chamados do cliente | `/clientes/conta/chamados` | Consultar e abrir chamados do cliente autenticado |
| Fotos | `/chamados/{id}/fotos`, `/clientes/conta/chamados/{id}/fotos` | Enviar fotos |

O painel administrativo requer um usuário ativo. A área do cliente requer conta criada pela tela “Cadastre-se como cliente”. Chamados, alterações de fase, materiais e fotos são gravados pela API no banco.

## Estrutura

```text
Arquitetura/banco.sql        Estrutura PostgreSQL
Backend/app/                 API FastAPI, modelos, autenticação e rotas
Backend/migrations/          Ajustes para bancos existentes
Backend/uploads/             Fotos dos chamados
Frontend/app.py              Interface Streamlit
Frontend/api.py              Cliente HTTP da API
Frontend/assets/             Estilos, interações e imagem da Defesa Civil
BI/                          Relatório Power BI
```
