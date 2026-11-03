# PulseDesk — frontend base

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

## O que está incluído

- Visão geral com indicadores, estado vazio e filtro de período por data de abertura, limite ou fechamento.
- Listagem de chamados com busca e filtro pelos status Chamados abertos, Em andamento, Aguardando retorno e Finalizado.
- Formulário para abertura de chamados, incluindo canal, prazo e preferências de notificação.
- Cadastros de clientes e tipos, e visualização dos usuários.
- Cadastros iniciam vazios, sem registros fictícios.
- Navegação lateral com ícones, realce discreto do módulo ativo e identificação da sessão no rodapé.
- Menu lateral organizado com a logo da Defesa Civil no topo, PulseDesk logo abaixo, navegação alinhada à esquerda e usuário no rodapé.
- Conteúdo principal centralizado para manter a composição da visão geral equilibrada em telas desktop.
- Período da visão geral sugerido do primeiro dia do mês atual até hoje.
- Paleta de verdes suaves e neutros, com tons semânticos reservados para status e boa legibilidade; configurações de tema em `.streamlit/config.toml`.
- Estilos em `assets/style.css` e script de interação em `assets/interactions.js`.

Esta é somente a camada de apresentação: os registros são mantidos em memória durante a sessão e não persistem após reiniciar o aplicativo. O perfil “Usuário conectado” é apenas um marcador visual, não uma autenticação. Persistência, autenticação, notificações e integração com uma API/banco de dados devem ser conectados em uma etapa posterior.
