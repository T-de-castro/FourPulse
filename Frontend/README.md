# Defesa Civil — central de atendimento

Protótipo de frontend para uma central de atendimento, construído com Streamlit. A estrutura acompanha as entidades do diagrama: usuários, clientes, tipos de chamado e chamados relacionados a clientes e tipos.

## Executar localmente

```bash
python -m venv .venv
```

No Windows:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Acesso demonstrativo

- E-mail: `representante@defesacivilconcordia.sc.gov.br`
- Senha: `Concórdia`

O acesso da equipe é demonstrativo e não substitui autenticação real. Os registros ficam em memória durante a sessão e não persistem após reiniciar o aplicativo.

Os campos da tela de login são preenchidos inicialmente com as credenciais de demonstração acima. Os rótulos usam português claro, com espaços entre as palavras e capitalização adequada. O cadastro de cliente permanece sem credenciais pré-preenchidas.
Novos clientes podem usar “Cadastre-se como cliente” e informar nome completo, CPF, e-mail e senha (mínimo de 8 caracteres). A senha é armazenada como hash com salt; após o cadastro, o cliente pode entrar em uma área restrita para ver apenas seus próprios dados e chamados ou abrir uma nova solicitação. A equipe mantém o acesso ao painel administrativo separado. Contas e chamados permanecem em memória durante a sessão e não persistem após reiniciar o aplicativo.

O protótipo inicia com clientes, categorias, materiais, usuários e chamados de exemplo para demonstrar os gráficos e o Kanban. Os dados são fictícios e podem ser alterados durante a sessão.

## Funcionalidades

- Visão geral com gráficos de barras horizontais para distribuição por fase e classificação, exibindo quantidades, percentuais e totais analisados.
- Quadro Kanban de chamados por fase, ordenado por abertura, com busca e filtros por fase/classificação.
- Cartões de ocorrência com ícones por classificação, badges acessíveis, metadados e diálogos para detalhes, atualização e finalização.
- Abertura de chamados com anexos de até 5 fotos; não há campo de prazo.
- Cadastro de clientes com CEP, bairro, rua e ponto de referência.
- Cadastro e login de clientes com acesso restrito aos módulos “Chamados” e “Novo chamado”.
- Cadastro de materiais com valor unitário e registro do material/quantidade usados ao finalizar chamados.
- Menu de usuário na barra lateral com opção para sair.
- Paleta administrativa com azul institucional, fundo cinza-claro e cores de fase consistentes, configurada em `.streamlit/config.toml`.
- Estilos em `assets/style.css` e script de interação em `assets/interactions.js`.
