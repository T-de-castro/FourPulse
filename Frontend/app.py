from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).parent
STATUSES = ["Chamados abertos", "Em andamento", "Aguardando retorno", "Finalizado"]
CHANNELS = ["WhatsApp", "E-mail", "Telefone", "Portal"]


def initial_data():
    return {
        "clients": [],
        "types": [],
        "users": [],
        "tickets": [],
        "next_ticket_id": 1,
    }


def setup_state():
    if st.session_state.get("data_schema_version") != 2:
        st.session_state.data = initial_data()
        st.session_state.data_schema_version = 2


def apply_styles():
    css_path = BASE_DIR / "assets" / "style.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_clock():
    js_path = BASE_DIR / "assets" / "interactions.js"
    script = js_path.read_text(encoding="utf-8")
    st.html(
        f"""<div class="clock-wrap"><span class="clock-dot"></span>
        <span id="live-clock">Carregando horário...</span></div>
        <style>
            .clock-wrap {{ color: #64736a;
                font: 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
            .clock-wrap {{ display: flex; align-items: center; gap: 8px; min-height: 28px; }}
            .clock-dot {{ width: 7px; height: 7px; border-radius: 50%; background: #22c55e; }}
        </style><script>{script}</script>""",
        unsafe_allow_javascript=True,
    )


def page_title(eyebrow, title, description, action_label=None, action_target=None):
    left, right = st.columns([5, 1.35], vertical_alignment="center")
    with left:
        st.markdown(
            f'<div class="eyebrow">{escape(eyebrow)}</div>'
            f'<h1 class="page-title">{escape(title)}</h1>'
            f'<div class="page-description">{escape(description)}</div>',
            unsafe_allow_html=True,
        )
    if action_label and action_target:
        with right:
            if st.button(action_label, type="primary", width="stretch", key="page_action"):
                st.session_state.navigation = action_target
                st.rerun()


def status_badge(status):
    classes = {
        "Chamados abertos": "open",
        "Em andamento": "progress",
        "Aguardando retorno": "waiting",
        "Finalizado": "done",
        "Ativo": "active",
        "Inativo": "inactive",
    }
    css_class = classes.get(status, "open")
    return f'<span class="status-badge {css_class}">{escape(status)}</span>'


def client_name(client_id):
    client = next((item for item in st.session_state.data["clients"] if item["id"] == client_id), None)
    return client["nome"] if client else "Cliente removido"


def type_name(type_id):
    item_type = next((item for item in st.session_state.data["types"] if item["id"] == type_id), None)
    return item_type["descricao"] if item_type else "Tipo removido"


def render_ticket_card(ticket):
    client = escape(client_name(ticket["cliente_id"]))
    category = escape(type_name(ticket["tipo_id"]))
    description = escape(ticket["descricao"])
    channel = escape(ticket["canal_entrada"])
    opened = escape(ticket["data_abertura"])
    status = status_badge(ticket["status"])
    st.markdown(
        f"""<div class="ticket-card">
            <div class="ticket-card-top">
                <div><span class="ticket-number">#{ticket["id"]}</span>
                <span class="ticket-category">{category}</span></div>{status}
            </div>
            <div class="ticket-description">{description}</div>
            <div class="ticket-meta">
                <span>◉ &nbsp;{client}</span><span>↗ &nbsp;{channel}</span>
                <span>◷ &nbsp;{opened}</span>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    if ticket["status"] != "Finalizado":
        if st.button("Marcar como finalizado", key=f"finish_{ticket['id']}"):
            ticket["status"] = "Finalizado"
            ticket["data_fechamento"] = date.today().strftime("%d/%m/%Y")
            st.rerun()


def ticket_date(ticket, date_field):
    value = ticket.get(date_field, "")
    if not value:
        return None
    formats = ("%d/%m/%Y %H:%M", "%d/%m/%Y")
    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    return None


def render_dashboard():
    data = st.session_state.data
    page_title("VISÃO GERAL", "Central de atendimento", "Acompanhe as solicitações e a operação em um só lugar.", "＋ Novo chamado", "Novo chamado")
    st.markdown('<div class="filter-panel"><div class="filter-heading">Filtrar chamados por período</div><div class="filter-caption">Escolha qual data do chamado usar no filtro.</div></div>', unsafe_allow_html=True)
    filter_columns = st.columns([1, 2.2])
    with filter_columns[0]:
        date_field = st.selectbox(
            "Considerar data de",
            ["Abertura", "Limite", "Fechamento"],
            key="dashboard_date_field",
        )
    with filter_columns[1]:
        today = date.today()
        selected_range = st.date_input(
            "Período",
            value=(today.replace(day=1), today),
            key="dashboard_date_range",
        )

    field_names = {
        "Abertura": "data_abertura",
        "Limite": "data_limite",
        "Fechamento": "data_fechamento",
    }
    if (
        isinstance(selected_range, tuple)
        and len(selected_range) == 2
        and all(isinstance(selected_date, date) for selected_date in selected_range)
    ):
        start_date, end_date = selected_range
        tickets = []
        for ticket in data["tickets"]:
            selected_date = ticket_date(ticket, field_names[date_field])
            if selected_date is not None and start_date <= selected_date <= end_date:
                tickets.append(ticket)
    else:
        tickets = []

    open_tickets = sum(ticket["status"] == "Chamados abertos" for ticket in tickets)
    in_progress = sum(ticket["status"] == "Em andamento" for ticket in tickets)
    waiting = sum(ticket["status"] == "Aguardando retorno" for ticket in tickets)
    completed = sum(ticket["status"] == "Finalizado" for ticket in tickets)

    cards = [
        ("Chamados abertos", open_tickets, "Aguardando atendimento", "blue", "◷"),
        ("Em andamento", in_progress, "Em atendimento pela equipe", "violet", "↗"),
        ("Aguardando retorno", waiting, "Dependem de uma resposta", "amber", "◉"),
        ("Finalizados", completed, "Solicitações resolvidas", "green", "✓"),
    ]
    columns = st.columns(4)
    for column, (label, value, caption, color, icon) in zip(columns, cards):
        with column:
            st.markdown(
                f"""<div class="metric-card">
                <div class="metric-top"><span>{escape(label)}</span><span class="metric-icon {color}">{icon}</span></div>
                <div class="metric-value">{value:02d}</div>
                <div class="metric-caption">{escape(caption)}</div></div>""",
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-heading"><div><h2>Chamados recentes</h2><p>Últimas solicitações registradas</p></div></div>', unsafe_allow_html=True)
    recent = sorted(tickets, key=lambda ticket: ticket["id"], reverse=True)[:3]
    if recent:
        for ticket in recent:
            render_ticket_card(ticket)
    else:
        st.markdown(
            '<div class="empty-state"><div class="empty-state-icon">◷</div>'
            '<div class="empty-state-title">Nenhum chamado neste período</div>'
            '<div class="empty-state-copy">Quando houver chamados cadastrados, eles aparecerão aqui.</div></div>',
            unsafe_allow_html=True,
        )


def render_tickets():
    page_title("ATENDIMENTO", "Chamados", "Consulte, filtre e acompanhe as solicitações.", "＋ Novo chamado", "Novo chamado")
    tickets = sorted(st.session_state.data["tickets"], key=lambda ticket: ticket["id"], reverse=True)
    search_col, status_col = st.columns([2.4, 1])
    with search_col:
        search = st.text_input("Buscar", placeholder="Busque por cliente, descrição ou número do chamado")
    with status_col:
        status_filter = st.selectbox("Status", ["Todos"] + STATUSES)

    filtered = []
    for ticket in tickets:
        searchable = f"{ticket['id']} {client_name(ticket['cliente_id'])} {ticket['descricao']}".casefold()
        if search.casefold() in searchable and (status_filter == "Todos" or ticket["status"] == status_filter):
            filtered.append(ticket)
    st.caption(f"{len(filtered)} chamado(s)")
    for ticket in filtered:
        render_ticket_card(ticket)
    if not filtered:
        st.markdown(
            '<div class="empty-state"><div class="empty-state-icon">◷</div>'
            '<div class="empty-state-title">Nenhum chamado encontrado</div>'
            '<div class="empty-state-copy">Ajuste os filtros ou cadastre um novo chamado.</div></div>',
            unsafe_allow_html=True,
        )


def render_new_ticket():
    page_title("ATENDIMENTO", "Novo chamado", "Registre uma solicitação e defina como o cliente deve ser notificado.")
    data = st.session_state.data
    if not data["clients"] or not data["types"]:
        st.warning("Cadastre pelo menos um cliente e um tipo antes de abrir um chamado.")
        return
    client_options = {client["nome"]: client["id"] for client in data["clients"]}
    type_options = {item_type["descricao"]: item_type["id"] for item_type in data["types"]}

    with st.form("new_ticket_form", clear_on_submit=True):
        first, second = st.columns(2)
        with first:
            selected_client = st.selectbox("Cliente", list(client_options))
            selected_type = st.selectbox("Tipo do chamado", list(type_options))
            channel = st.selectbox("Canal de entrada", CHANNELS)
        with second:
            status = st.selectbox("Status inicial", STATUSES, index=0)
            deadline = st.date_input("Data limite", value=date.today() + timedelta(days=2))
            notify_whatsapp = st.checkbox("Notificar por WhatsApp")
            notify_email = st.checkbox("Notificar por e-mail")
        description = st.text_area("Descrição", placeholder="Descreva a solicitação com o máximo de contexto possível.", height=130)
        submitted = st.form_submit_button("Criar chamado", type="primary", width="stretch")
        if submitted:
            if not description.strip():
                st.error("Informe uma descrição para o chamado.")
            else:
                ticket_id = data["next_ticket_id"]
                data["tickets"].append(
                    {
                        "id": ticket_id,
                        "cliente_id": client_options[selected_client],
                        "tipo_id": type_options[selected_type],
                        "data_abertura": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "data_limite": deadline.strftime("%d/%m/%Y"),
                        "data_fechamento": "",
                        "canal_entrada": channel,
                        "status": status,
                        "descricao": description.strip(),
                        "notificar_whatsapp": notify_whatsapp,
                        "notificar_email": notify_email,
                    }
                )
                data["next_ticket_id"] += 1
                st.success(f"Chamado #{ticket_id} criado.")
                st.session_state.navigation = "Chamados"
                st.rerun()


def render_clients():
    page_title("CADASTROS", "Clientes", "Gerencie os dados de contato dos clientes.")
    with st.expander("＋ Cadastrar cliente", expanded=False):
        with st.form("new_client_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nome")
                cpf = st.text_input("CPF")
                email = st.text_input("E-mail")
            with col2:
                whatsapp = st.text_input("WhatsApp")
                age = st.number_input("Idade", min_value=0, max_value=120, value=18)
                state = st.text_input("Estado (UF)", max_chars=2)
            submitted = st.form_submit_button("Salvar cliente", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Informe o nome do cliente.")
                else:
                    clients = st.session_state.data["clients"]
                    clients.append(
                        {
                            "id": max((client["id"] for client in clients), default=0) + 1,
                            "nome": name.strip(),
                            "cpf": cpf.strip(),
                            "email": email.strip(),
                            "whatsapp": whatsapp.strip(),
                            "idade": int(age),
                            "estado": state.strip().upper(),
                            "status": "Ativo",
                        }
                    )
                    st.success("Cliente cadastrado.")
                    st.rerun()

    clients = st.session_state.data["clients"]
    st.caption(f"{len(clients)} cliente(s) cadastrado(s)")
    if not clients:
        st.markdown(
            '<div class="empty-state"><div class="empty-state-icon">◉</div>'
            '<div class="empty-state-title">Nenhum cliente cadastrado</div>'
            '<div class="empty-state-copy">Use “Cadastrar cliente” para adicionar o primeiro registro.</div></div>',
            unsafe_allow_html=True,
        )
    for client in clients:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**{client['nome']}**")
                st.caption(f"CPF: {client['cpf'] or 'Não informado'} · {client['estado'] or 'UF não informada'}")
            with col2:
                st.write(client["email"] or "E-mail não informado")
                st.caption(client["whatsapp"] or "WhatsApp não informado")
            with col3:
                st.markdown(status_badge(client["status"]), unsafe_allow_html=True)


def render_types():
    page_title("CONFIGURAÇÕES", "Tipos de chamado", "Organize as solicitações por categoria.")
    with st.form("new_type_form", clear_on_submit=True):
        description = st.text_input("Descrição do tipo", placeholder="Ex.: Suporte técnico")
        submitted = st.form_submit_button("＋ Adicionar tipo", type="primary")
        if submitted:
            if not description.strip():
                st.error("Informe a descrição do tipo.")
            elif any(item["descricao"].casefold() == description.strip().casefold() for item in st.session_state.data["types"]):
                st.error("Este tipo já está cadastrado.")
            else:
                types = st.session_state.data["types"]
                types.append({"id": max((item["id"] for item in types), default=0) + 1, "descricao": description.strip()})
                st.success("Tipo adicionado.")
                st.rerun()

    types = st.session_state.data["types"]
    if not types:
        st.markdown(
            '<div class="empty-state"><div class="empty-state-icon">▦</div>'
            '<div class="empty-state-title">Nenhum tipo cadastrado</div>'
            '<div class="empty-state-copy">Adicione uma categoria para organizar os chamados.</div></div>',
            unsafe_allow_html=True,
        )
    for item_type in types:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{item_type['descricao']}**")
                st.caption(f"ID do tipo: {item_type['id']}")
            with col2:
                count = sum(ticket["tipo_id"] == item_type["id"] for ticket in st.session_state.data["tickets"])
                st.metric("Chamados", count)


def render_users():
    page_title("CONFIGURAÇÕES", "Usuários", "Visualize os acessos da equipe de atendimento.")
    users = st.session_state.data["users"]
    st.caption(f"{len(users)} usuário(s) cadastrado(s)")
    if not users:
        st.markdown(
            '<div class="empty-state"><div class="empty-state-icon">♙</div>'
            '<div class="empty-state-title">Nenhum usuário cadastrado</div>'
            '<div class="empty-state-copy">Os usuários disponíveis serão exibidos aqui.</div></div>',
            unsafe_allow_html=True,
        )
    for user in users:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**{user['nome']}**")
                st.caption(f"CPF: {user['cpf']}")
            with col2:
                st.write(user["permissao"])
                st.caption(f"ID do usuário: {user['id']}")
            with col3:
                st.markdown(status_badge(user["status"]), unsafe_allow_html=True)


st.set_page_config(page_title="PulseDesk | Atendimento", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
setup_state()
apply_styles()

with st.sidebar:
    with st.container(key="sidebar-layout"):
        st.image(
            str(BASE_DIR / "assets" / "defesa_civil_concordia.jpeg"),
            width=90,
            alt="Logo da Defesa Civil de Concórdia, Santa Catarina",
        )
        st.markdown(
            '<div class="brand"><div class="brand-name">PulseDesk</div>'
            '<div class="brand-caption">CENTRAL DE ATENDIMENTO</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-label">MENU PRINCIPAL</div>', unsafe_allow_html=True)
        pages = [
            ("Visão geral", ":material/dashboard:"),
            ("Chamados", ":material/confirmation_number:"),
            ("Novo chamado", ":material/add_circle:"),
            ("Clientes", ":material/group:"),
            ("Tipos", ":material/category:"),
            ("Usuários", ":material/manage_accounts:"),
        ]
        if "navigation" not in st.session_state:
            st.session_state.navigation = "Visão geral"
        for page, icon in pages:
            if st.button(
                page,
                icon=icon,
                key=f"navigation_{page}",
                type="primary" if st.session_state.navigation == page else "secondary",
                width="stretch",
            ):
                st.session_state.navigation = page
                st.rerun()
        with st.container(key="sidebar-profile"):
            st.markdown(
                '<div class="user-profile"><div class="avatar">UC</div><div><strong>Usuário conectado</strong>'
                '<span>Sessão atual</span></div></div>',
                unsafe_allow_html=True,
            )
        selected_page = st.session_state.navigation

page_renderers = {
    "Visão geral": render_dashboard,
    "Chamados": render_tickets,
    "Novo chamado": render_new_ticket,
    "Clientes": render_clients,
    "Tipos": render_types,
    "Usuários": render_users,
}
page_renderers[selected_page]()
