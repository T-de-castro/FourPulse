from collections import Counter
from datetime import date, datetime, timedelta
import hashlib
import hmac
from html import escape
from pathlib import Path
import re
import secrets

import altair as alt
import streamlit as st


BASE_DIR = Path(__file__).parent
STATUSES = ["Chamados abertos", "Em andamento", "Aguardando retorno", "Finalizado"]
CHANNELS = ["WhatsApp", "E-mail", "Telefone", "Portal"]
DEMO_EMAIL = "representante@defesacivilconcordia.sc.gov.br"
DEMO_PASSWORD = "Concórdia"
DEMO_USER = "Representante da Defesa Civil"
PASSWORD_HASH_ITERATIONS = 310_000
PASSWORD_SALT_BYTES = 16
STATUS_PRESENTATION = {
    "Chamados abertos": {
        "label": "Aberto",
        "icon": "schedule",
        "color": "orange",
        "class": "open",
        "hex": "#B45309",
    },
    "Em andamento": {
        "label": "Em andamento",
        "icon": "sync",
        "color": "blue",
        "class": "progress",
        "hex": "#1D4ED8",
    },
    "Aguardando retorno": {
        "label": "Aguardando retorno",
        "icon": "hourglass_top",
        "color": "violet",
        "class": "waiting",
        "hex": "#6D28D9",
    },
    "Finalizado": {
        "label": "Finalizado",
        "icon": "task_alt",
        "color": "green",
        "class": "done",
        "hex": "#15803D",
    },
}
STATUS_COLORS = [STATUS_PRESENTATION[status]["hex"] for status in STATUSES]
CLASSIFICATION_ICONS = {
    "alagamento": "flood",
    "deslizamento": "landslide",
    "risco estrutural": "foundation",
    "incêndio": "local_fire_department",
    "incendio": "local_fire_department",
    "queda de árvore": "forest",
    "queda de arvore": "forest",
    "vendaval": "thunderstorm",
    "tempestade": "thunderstorm",
    "apoio": "volunteer_activism",
    "assistência": "volunteer_activism",
    "assistencia": "volunteer_activism",
    "outras ocorrências": "report_problem",
    "outras ocorrencias": "report_problem",
}
CHANNEL_ICONS = {
    "whatsapp": "chat",
    "e-mail": "mail",
    "telefone": "call",
    "portal": "language",
}


def initial_data():
    now = datetime.now()
    return {
        "clients": [
            {
                "id": 1,
                "nome": "Ana Martins",
                "cpf": "123.456.789-00",
                "email": "ana.martins@example.com",
                "whatsapp": "(49) 99912-3456",
                "idade": 38,
                "estado": "SC",
                "cep": "89700-100",
                "bairro": "Centro",
                "rua": "Rua das Araucárias, 120",
                "ponto_referencia": "Próximo à praça central",
                "status": "Ativo",
            },
            {
                "id": 2,
                "nome": "João da Silva",
                "cpf": "234.567.890-11",
                "email": "joao.silva@example.com",
                "whatsapp": "(49) 99876-5432",
                "idade": 52,
                "estado": "SC",
                "cep": "89700-210",
                "bairro": "Imperial",
                "rua": "Rua dos Pioneiros, 45",
                "ponto_referencia": "Ao lado do posto de saúde",
                "status": "Ativo",
            },
            {
                "id": 3,
                "nome": "Mariana Costa",
                "cpf": "345.678.901-22",
                "email": "mariana.costa@example.com",
                "whatsapp": "(49) 99765-4321",
                "idade": 29,
                "estado": "SC",
                "cep": "89700-330",
                "bairro": "Santa Cruz",
                "rua": "Avenida do Comércio, 870",
                "ponto_referencia": "Casa com portão azul",
                "status": "Ativo",
            },
        ],
        "types": [
            {"id": 1, "descricao": "Alagamento"},
            {"id": 2, "descricao": "Queda de árvore"},
            {"id": 3, "descricao": "Deslizamento"},
            {"id": 4, "descricao": "Risco estrutural"},
        ],
        "users": [
            {
                "id": 1,
                "nome": DEMO_USER,
                "email": DEMO_EMAIL,
                "permissao": "Administrador",
                "status": "Ativo",
            },
            {
                "id": 2,
                "nome": "Agente João Ribeiro",
                "email": "joao.ribeiro@example.com",
                "permissao": "Atendente",
                "status": "Ativo",
            },
            {
                "id": 3,
                "nome": "Agente Paula Mendes",
                "email": "paula.mendes@example.com",
                "permissao": "Atendente",
                "status": "Ativo",
            },
        ],
        "customer_accounts": [],
        "materials": [
            {"id": 1, "descricao": "Lona plástica reforçada", "valor": 85.0},
            {"id": 2, "descricao": "Kit de limpeza", "valor": 42.5},
            {"id": 3, "descricao": "Saco de areia", "valor": 8.0},
            {"id": 4, "descricao": "Fita de sinalização", "valor": 19.9},
        ],
        "tickets": [
            {
                "id": 1,
                "cliente_id": 1,
                "tipo_id": 1,
                "data_abertura": (now - timedelta(hours=2)).strftime("%d/%m/%Y %H:%M"),
                "data_fechamento": "",
                "canal_entrada": "Telefone",
                "status": "Chamados abertos",
                "descricao": "Água acumulando na entrada da residência após a chuva.",
                "notificar_whatsapp": True,
                "notificar_email": False,
                "fotos": [],
                "materiais_utilizados": [],
            },
            {
                "id": 2,
                "cliente_id": 2,
                "tipo_id": 2,
                "data_abertura": (now - timedelta(hours=5)).strftime("%d/%m/%Y %H:%M"),
                "data_fechamento": "",
                "canal_entrada": "WhatsApp",
                "status": "Em andamento",
                "descricao": "Galho de grande porte caiu sobre a via e bloqueia parcialmente a passagem.",
                "notificar_whatsapp": True,
                "notificar_email": False,
                "fotos": [],
                "materiais_utilizados": [],
            },
            {
                "id": 3,
                "cliente_id": 3,
                "tipo_id": 3,
                "data_abertura": (now - timedelta(days=1)).strftime("%d/%m/%Y %H:%M"),
                "data_fechamento": "",
                "canal_entrada": "Portal",
                "status": "Aguardando retorno",
                "descricao": "Pequena movimentação de terra observada no talude nos fundos do terreno.",
                "notificar_whatsapp": False,
                "notificar_email": True,
                "fotos": [],
                "materiais_utilizados": [],
            },
            {
                "id": 4,
                "cliente_id": 1,
                "tipo_id": 4,
                "data_abertura": (now - timedelta(days=2)).strftime("%d/%m/%Y %H:%M"),
                "data_fechamento": "",
                "canal_entrada": "Telefone",
                "status": "Chamados abertos",
                "descricao": "Trinca recente em parede externa após período de chuva intensa.",
                "notificar_whatsapp": True,
                "notificar_email": True,
                "fotos": [],
                "materiais_utilizados": [],
            },
            {
                "id": 5,
                "cliente_id": 2,
                "tipo_id": 1,
                "data_abertura": (now - timedelta(days=3)).strftime("%d/%m/%Y %H:%M"),
                "data_fechamento": (now - timedelta(days=2)).strftime("%d/%m/%Y"),
                "canal_entrada": "E-mail",
                "status": "Finalizado",
                "descricao": "Apoio com lona e materiais de limpeza após entrada de água na garagem.",
                "notificar_whatsapp": False,
                "notificar_email": True,
                "fotos": [],
                "materiais_utilizados": [
                    {
                        "material_id": 1,
                        "descricao": "Lona plástica reforçada",
                        "quantidade": 1,
                        "valor_unitario": 85.0,
                    },
                    {
                        "material_id": 2,
                        "descricao": "Kit de limpeza",
                        "quantidade": 2,
                        "valor_unitario": 42.5,
                    },
                ],
            },
        ],
        "next_ticket_id": 6,
    }


def setup_state():
    if st.session_state.get("data_schema_version") != 5:
        st.session_state.data = initial_data()
        st.session_state.data_schema_version = 5
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("navigation", "Visão geral")
    st.session_state.setdefault("active_ticket_dialog", None)


def hash_customer_password(password, salt=None):
    salt = salt or secrets.token_bytes(PASSWORD_SALT_BYTES)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return salt.hex(), password_hash.hex()


def authenticate_customer(email, password):
    account = next(
        (
            item
            for item in st.session_state.data["customer_accounts"]
            if item["email"].casefold() == email.strip().casefold()
        ),
        None,
    )
    if account is None:
        return None

    salt = bytes.fromhex(account["password_salt"])
    _, password_hash = hash_customer_password(password, salt)
    if not hmac.compare_digest(password_hash, account["password_hash"]):
        return None

    return next(
        (
            client
            for client in st.session_state.data["clients"]
            if client["id"] == account["client_id"]
        ),
        None,
    )


def logout_user():
    st.session_state.authenticated = False
    st.session_state.pop("user_role", None)
    st.session_state.pop("user_name", None)
    st.session_state.pop("user_email", None)
    st.session_state.pop("client_id", None)
    st.session_state.active_ticket_dialog = None
    st.session_state.navigation = "Visão geral"
    st.rerun()


def is_valid_cpf(value):
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False

    first_digit = sum(int(digits[index]) * (10 - index) for index in range(9)) % 11
    first_digit = 0 if first_digit < 2 else 11 - first_digit
    second_digit = sum(int(digits[index]) * (11 - index) for index in range(10)) % 11
    second_digit = 0 if second_digit < 2 else 11 - second_digit
    return digits[-2:] == f"{first_digit}{second_digit}"


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
            .clock-wrap {{ color: #64748b;
                font: 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
            .clock-wrap {{ display: flex; align-items: center; gap: 8px; min-height: 28px; }}
            .clock-dot {{ width: 7px; height: 7px; border-radius: 50%; background: #1D4ED8; }}
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
            if st.button(action_label, type="primary", width="stretch"):
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


def status_presentation(status):
    return STATUS_PRESENTATION.get(status, STATUS_PRESENTATION["Chamados abertos"])


def classification_icon(name):
    return CLASSIFICATION_ICONS.get(name.strip().casefold(), "report_problem")


def horizontal_bar_chart(data, category_field, category_label, colors):
    domain_max = max(max(row["quantidade"] for row in data), 1) * 1.5
    category_colors = [colors[index % len(colors)] for index in range(len(data))]
    category_order = [row[category_field] for row in data]
    chart_data = [
        {
            **row,
            "rotulo": f"{row['quantidade']} · {row['percentual']:.1f}%",
            "posicao_rotulo": domain_max * 0.98,
        }
        for row in data
    ]
    source = alt.Chart(alt.Data(values=chart_data))
    bars = source.mark_bar(size=22, cornerRadiusEnd=4).encode(
        x=alt.X(
            "quantidade:Q",
            scale=alt.Scale(domain=[0, domain_max], nice=False),
            axis=alt.Axis(
                title=None,
                tickMinStep=1,
                grid=True,
                gridColor="#E2E8F0",
                domain=False,
            ),
        ),
        y=alt.Y(
            f"{category_field}:N",
            sort=category_order,
            axis=alt.Axis(
                title=None,
                domain=False,
                ticks=False,
                labelLimit=190,
                labelPadding=9,
            ),
        ),
        color=alt.Color(
            f"{category_field}:N",
            scale=alt.Scale(
                domain=[row[category_field] for row in chart_data],
                range=category_colors,
            ),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip(f"{category_field}:N", title=category_label),
            alt.Tooltip("quantidade:Q", title="Chamados"),
            alt.Tooltip("rotulo:N", title="Percentual do total"),
        ],
    )
    labels = source.mark_text(
        align="right",
        baseline="middle",
        fontSize=12,
        fontWeight="bold",
        color="#334155",
    ).encode(
        x=alt.X(
            "posicao_rotulo:Q",
            scale=alt.Scale(domain=[0, domain_max], nice=False),
            axis=None,
        ),
        y=alt.Y(
            f"{category_field}:N",
            sort=category_order,
        ),
        text=alt.Text("rotulo:N"),
    )
    return (
        alt.layer(bars, labels)
        .properties(height=max(132, 42 * len(chart_data)))
        .configure_view(stroke=None)
    )


def ticket_opened_datetime(ticket):
    value = ticket.get("data_abertura", "")
    for date_format in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    return datetime.min


def can_update_tickets():
    if not st.session_state.get("authenticated"):
        return False
    email = st.session_state.get("user_email")
    user = next(
        (item for item in st.session_state.data["users"] if item.get("email") == email),
        None,
    )
    return bool(user and user["permissao"] in {"Administrador", "Atendente"})


def open_ticket_dialog(dialog_type, ticket_id):
    st.session_state.active_ticket_dialog = (dialog_type, ticket_id)
    st.rerun()


def client_name(client_id):
    client = next((item for item in st.session_state.data["clients"] if item["id"] == client_id), None)
    return client["nome"] if client else "Cliente removido"


def type_name(type_id):
    item_type = next((item for item in st.session_state.data["types"] if item["id"] == type_id), None)
    return item_type["descricao"] if item_type else "Tipo removido"


def material_by_id(material_id):
    return next(
        (item for item in st.session_state.data["materials"] if item["id"] == material_id),
        None,
    )


def save_ticket_phase(ticket, new_status, selected_material_id=None, quantity=0):
    if new_status == "Finalizado":
        if selected_material_id is not None and quantity <= 0:
            st.error("A quantidade do material deve ser maior que zero.")
            return
        if selected_material_id is not None:
            material = material_by_id(selected_material_id)
            if material is None:
                st.error("O material selecionado não está mais cadastrado.")
                return
            ticket.setdefault("materiais_utilizados", []).append(
                {
                    "material_id": material["id"],
                    "descricao": material["descricao"],
                    "quantidade": quantity,
                    "valor_unitario": material["valor"],
                }
            )
        ticket["data_fechamento"] = date.today().strftime("%d/%m/%Y")
    ticket["status"] = new_status
    st.session_state.flash_success = f"Chamado #{ticket['id']} atualizado para {status_presentation(new_status)['label']}."
    st.session_state.active_ticket_dialog = None
    st.rerun()


def render_ticket_card(ticket, compact=False):
    ticket_id = ticket["id"]
    client = client_name(ticket["cliente_id"])
    category = type_name(ticket["tipo_id"])
    phase = status_presentation(ticket["status"])
    classification_symbol = classification_icon(category)
    channel_symbol = CHANNEL_ICONS.get(ticket["canal_entrada"].casefold(), "support_agent")
    ticket_key = f"ticket-card-{ticket_id}"

    with st.container(border=True, key=ticket_key):
        heading_col, phase_col = st.columns([5, 1.7], vertical_alignment="center")
        with heading_col:
            with st.container(key=f"ticket-classification-{phase['class']}-{ticket_id}"):
                st.badge(category, icon=f":material/{classification_symbol}:", color=phase["color"])
            st.markdown(f"**Chamado #{ticket_id}**")
        with phase_col:
            with st.container(key=f"ticket-phase-{phase['class']}-{ticket_id}"):
                st.badge(phase["label"], icon=f":material/{phase['icon']}:", color="gray")

        st.markdown("**Descrição**")
        st.write(ticket.get("descricao", "Descrição não informada"))

        solicitant_col, channel_col, opened_col = st.columns(3)
        with solicitant_col:
            st.markdown(f":material/person: **Solicitante**  \n{client}")
        with channel_col:
            st.markdown(
                f":material/{channel_symbol}: **Canal**  \n{ticket['canal_entrada']}"
            )
        with opened_col:
            st.markdown(
                f":material/calendar_month: **Abertura**  \n{ticket['data_abertura']}"
            )

        used_materials = ticket.get("materiais_utilizados", [])
        if used_materials:
            st.caption(
                "Materiais registrados: "
                + ", ".join(
                    f"{item['descricao']} — {item['quantidade']} un."
                    for item in used_materials
                )
            )

        st.markdown('<div class="ticket-card-divider"></div>', unsafe_allow_html=True)
        if compact:
            if st.button(
                "Ver detalhes",
                icon=":material/visibility:",
                key=f"ticket_details_{ticket_id}",
                width="stretch",
            ):
                open_ticket_dialog("details", ticket_id)
            if can_update_tickets() and ticket["status"] != "Finalizado":
                if st.button(
                    "Atualizar fase",
                    icon=":material/sync:",
                    key=f"ticket_update_{ticket_id}",
                    width="stretch",
                ):
                    open_ticket_dialog("phase", ticket_id)
                if st.button(
                    "Finalizar chamado",
                    icon=":material/task_alt:",
                    key=f"ticket_finish_{ticket_id}",
                    width="stretch",
                ):
                    open_ticket_dialog("finish", ticket_id)
        else:
            action_columns = st.columns(3)
            with action_columns[0]:
                if st.button(
                    "Ver detalhes",
                    icon=":material/visibility:",
                    key=f"ticket_details_{ticket_id}",
                    width="stretch",
                ):
                    open_ticket_dialog("details", ticket_id)
            if can_update_tickets() and ticket["status"] != "Finalizado":
                with action_columns[1]:
                    if st.button(
                        "Atualizar fase",
                        icon=":material/sync:",
                        key=f"ticket_update_{ticket_id}",
                        width="stretch",
                    ):
                        open_ticket_dialog("phase", ticket_id)
                with action_columns[2]:
                    if st.button(
                        "Finalizar chamado",
                        icon=":material/task_alt:",
                        key=f"ticket_finish_{ticket_id}",
                        width="stretch",
                    ):
                        open_ticket_dialog("finish", ticket_id)


def find_ticket(ticket_id):
    return next(
        (ticket for ticket in st.session_state.data["tickets"] if ticket["id"] == ticket_id),
        None,
    )


@st.dialog("Detalhes do chamado", width="large", dismissible=False)
def show_ticket_details(ticket_id):
    ticket = find_ticket(ticket_id)
    if ticket is None:
        st.error("Este chamado não foi encontrado.")
        return

    phase = status_presentation(ticket["status"])
    st.badge(phase["label"], icon=f":material/{phase['icon']}:", color=phase["color"])
    st.subheader(f"{type_name(ticket['tipo_id'])} · Chamado #{ticket_id}")
    st.markdown("**Descrição completa**")
    st.write(ticket.get("descricao", "Descrição não informada"))
    client = next(
        (item for item in st.session_state.data["clients"] if item["id"] == ticket["cliente_id"]),
        None,
    )
    if client:
        st.markdown(f"**Solicitante:** {client['nome']}")
        address = ", ".join(
            value
            for value in [
                client.get("rua", ""),
                client.get("bairro", ""),
                client.get("cep", ""),
                client.get("estado", ""),
            ]
            if value
        )
        if address:
            st.markdown(f"**Endereço:** {address}")
        if client.get("ponto_referencia"):
            st.markdown(f"**Ponto de referência:** {client['ponto_referencia']}")
    st.markdown(f"**Canal:** {ticket['canal_entrada']}")
    st.markdown(f"**Abertura:** {ticket['data_abertura']}")
    if ticket.get("data_fechamento"):
        st.markdown(f"**Finalizado em:** {ticket['data_fechamento']}")

    photos = ticket.get("fotos", [])
    if photos:
        st.markdown("**Fotos anexadas**")
        st.image(
            [photo["conteudo"] for photo in photos],
            caption=[photo["nome"] for photo in photos],
            alt=[f"Foto anexada ao chamado {ticket_id}" for _ in photos],
            width="stretch",
        )

    materials = ticket.get("materiais_utilizados", [])
    if materials:
        st.markdown("**Materiais utilizados**")
        for material in materials:
            total = material["valor_unitario"] * material["quantidade"]
            st.write(
                f"{material['descricao']} — {material['quantidade']} un. "
                f"× R$ {material['valor_unitario']:.2f} = R$ {total:.2f}"
            )
    if st.button("Fechar detalhes", key=f"details_close_{ticket_id}"):
        st.session_state.active_ticket_dialog = None
        st.rerun()


@st.dialog("Atualizar fase", width="small", dismissible=False)
def show_ticket_phase_dialog(ticket_id):
    ticket = find_ticket(ticket_id)
    if ticket is None:
        st.error("Este chamado não foi encontrado.")
        return
    if ticket["status"] == "Finalizado":
        st.info("Chamados finalizados não podem ter a fase alterada.")
        return

    current = status_presentation(ticket["status"])
    st.markdown(f"**Fase atual:** {current['label']}")
    allowed_statuses = [status for status in STATUSES if status != "Finalizado"]
    selected_status = st.selectbox(
        "Nova fase",
        allowed_statuses,
        index=allowed_statuses.index(ticket["status"]),
        format_func=lambda status: status_presentation(status)["label"],
        key=f"phase_dialog_select_{ticket_id}",
    )
    save_col, cancel_col = st.columns(2)
    with save_col:
        if st.button(
            "Confirmar atualização",
            type="primary",
            key=f"phase_dialog_save_{ticket_id}",
            width="stretch",
        ):
            if selected_status == ticket["status"]:
                st.info("Selecione uma fase diferente da fase atual.")
            else:
                save_ticket_phase(ticket, selected_status)
    with cancel_col:
        if st.button("Cancelar", key=f"phase_dialog_cancel_{ticket_id}", width="stretch"):
            st.session_state.active_ticket_dialog = None
            st.rerun()


@st.dialog("Finalizar chamado", width="small", dismissible=False)
def show_ticket_finish_dialog(ticket_id):
    ticket = find_ticket(ticket_id)
    if ticket is None:
        st.error("Este chamado não foi encontrado.")
        return
    if ticket["status"] == "Finalizado":
        st.info("Este chamado já está finalizado.")
        return

    current = status_presentation(ticket["status"])
    st.markdown(f"**Fase atual:** {current['label']}")
    st.write("Confirme o encerramento e informe os materiais utilizados, se houver.")
    materials = st.session_state.data["materials"]
    options = {"Não informar material": None}
    options.update({material["descricao"]: material["id"] for material in materials})
    selected_label = st.selectbox(
        "Material utilizado",
        list(options),
        key=f"finish_material_{ticket_id}",
    )
    quantity = 0
    if options[selected_label] is not None:
        quantity = st.number_input(
            "Quantidade utilizada",
            min_value=1,
            step=1,
            value=1,
            key=f"finish_quantity_{ticket_id}",
        )
    if not materials:
        st.caption("Não há materiais cadastrados. O chamado poderá ser finalizado sem material.")
    confirmed = st.checkbox(
        "Confirmo o encerramento deste chamado",
        key=f"finish_confirm_{ticket_id}",
    )
    finish_col, cancel_col = st.columns(2)
    with finish_col:
        if st.button(
            "Confirmar finalização",
            type="primary",
            key=f"finish_confirm_button_{ticket_id}",
            width="stretch",
        ):
            if not confirmed:
                st.error("Confirme o encerramento antes de continuar.")
            else:
                save_ticket_phase(
                    ticket,
                    "Finalizado",
                    options[selected_label],
                    int(quantity),
                )
    with cancel_col:
        if st.button("Cancelar", key=f"finish_cancel_{ticket_id}", width="stretch"):
            st.session_state.active_ticket_dialog = None
            st.rerun()


def render_login():
    st.session_state.setdefault("login_view", "login")
    view = st.session_state.login_view
    screen_title = "Cadastre-se" if view == "register" else "Central de Atendimento"
    screen_description = (
        "Crie seu acesso de cliente para acompanhar seus chamados."
        if view == "register"
        else "Acesse sua conta para acompanhar as ocorrências."
    )

    with st.container(key="login-page"):
        with st.container(border=True, key="login-card"):
            logo_columns = st.columns([1, 1, 1])
            with logo_columns[1]:
                st.image(
                    str(BASE_DIR / "assets" / "defesa_civil_concordia.jpeg"),
                    width=148,
                    alt="Logo oficial da Defesa Civil de Concórdia",
                )
            st.markdown(
                '<div class="login-eyebrow">DEFESA CIVIL DE CONCÓRDIA · SC</div>'
                f'<h1 class="login-title">{screen_title}</h1>'
                f'<div class="login-description">{screen_description}</div>',
                unsafe_allow_html=True,
            )
            if view == "register":
                with st.form("client_registration_form", clear_on_submit=False, border=False):
                    name = st.text_input("Nome completo", key="registration_name")
                    cpf = st.text_input(
                        "CPF",
                        key="registration_cpf",
                        placeholder="000.000.000-00",
                    )
                    email = st.text_input(
                        "E-mail",
                        key="registration_email",
                        type="email",
                        placeholder="nome@exemplo.com",
                    )
                    password = st.text_input(
                        "Senha",
                        key="registration_password",
                        type="password",
                        help="Use pelo menos 8 caracteres.",
                    )
                    submitted = st.form_submit_button(
                        "Cadastrar",
                        type="primary",
                        icon=":material/person_add:",
                        width="stretch",
                    )
                if submitted:
                    normalized_email = email.strip().casefold()
                    clients = st.session_state.data["clients"]
                    existing_email = any(
                        client.get("email", "").strip().casefold() == normalized_email
                        for client in clients
                        if normalized_email
                    )
                    existing_staff_email = any(
                        user.get("email", "").strip().casefold() == normalized_email
                        for user in st.session_state.data["users"]
                        if normalized_email
                    )
                    cpf_digits = re.sub(r"\D", "", cpf)
                    existing_cpf = any(
                        re.sub(r"\D", "", client.get("cpf", "")) == cpf_digits
                        for client in clients
                    )
                    if not name.strip():
                        st.error("Informe seu nome completo.")
                    elif not is_valid_cpf(cpf):
                        st.error("Informe um CPF válido.")
                    elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized_email):
                        st.error("Informe um E-mail válido.")
                    elif existing_email or existing_staff_email:
                        st.error("Já existe um cadastro com esse E-mail.")
                    elif existing_cpf:
                        st.error("Já existe um cadastro com esse CPF.")
                    elif len(password) < 8:
                        st.error("A Senha deve ter pelo menos 8 caracteres.")
                    else:
                        password_salt, password_hash = hash_customer_password(password)
                        client_id = max(
                            (client["id"] for client in clients),
                            default=0,
                        ) + 1
                        clients.append(
                            {
                                "id": client_id,
                                "nome": name.strip(),
                                "cpf": cpf_digits,
                                "email": email.strip(),
                                "whatsapp": "",
                                "idade": None,
                                "estado": "",
                                "cep": "",
                                "bairro": "",
                                "rua": "",
                                "ponto_referencia": "",
                                "status": "Ativo",
                            }
                        )
                        st.session_state.data["customer_accounts"].append(
                            {
                                "client_id": client_id,
                                "email": normalized_email,
                                "password_salt": password_salt,
                                "password_hash": password_hash,
                            }
                        )
                        st.session_state.flash_registration = (
                            "Cadastro concluído. Entre com seu E-mail e sua Senha."
                        )
                        st.session_state.login_view = "login"
                        st.rerun()
                if st.button(
                    "Voltar para Entrar",
                    key="registration_back_to_login",
                    width="stretch",
                ):
                    st.session_state.login_view = "login"
                    st.rerun()
            else:
                with st.form("login_form", clear_on_submit=False, border=False):
                    email = st.text_input(
                        "E-mail",
                        value=DEMO_EMAIL,
                        key="login_email",
                        type="email",
                        placeholder="nome@exemplo.com",
                    )
                    password = st.text_input(
                        "Senha",
                        value=DEMO_PASSWORD,
                        key="login_password",
                        type="password",
                        placeholder="Digite sua senha",
                    )
                    submitted = st.form_submit_button(
                        "Entrar",
                        type="primary",
                        icon=":material/login:",
                        width="stretch",
                    )
                if submitted:
                    if not email.strip() and not password:
                        st.error("Informe seu E-mail e sua Senha.")
                    elif not email.strip():
                        st.error("Informe seu E-mail.")
                    elif not password:
                        st.error("Informe sua Senha.")
                    else:
                        with st.spinner("Validando seu acesso..."):
                            if (
                                email.strip().casefold() == DEMO_EMAIL.casefold()
                                and password == DEMO_PASSWORD
                            ):
                                st.session_state.authenticated = True
                                st.session_state.user_role = "staff"
                                st.session_state.user_name = DEMO_USER
                                st.session_state.user_email = DEMO_EMAIL
                                st.rerun()
                            client = authenticate_customer(email, password)
                            if client:
                                st.session_state.authenticated = True
                                st.session_state.user_role = "client"
                                st.session_state.user_name = client["nome"]
                                st.session_state.user_email = client["email"]
                                st.session_state.client_id = client["id"]
                                st.rerun()
                            st.error("E-mail ou senha inválidos. Confira os dados e tente novamente.")
                if "flash_registration" in st.session_state:
                    st.success(st.session_state.pop("flash_registration"))
                if st.button(
                    "Cadastre-se como cliente",
                    key="open_client_registration",
                    icon=":material/person_add:",
                    width="stretch",
                ):
                    st.session_state.login_view = "register"
                    st.rerun()


def render_customer_ticket_form(client):
    data = st.session_state.data
    if not data["types"]:
        st.info("Não há classificações disponíveis para abrir um chamado.")
        return

    st.markdown('<div class="section-heading"><div><h2>Novo chamado</h2></div></div>', unsafe_allow_html=True)
    type_options = {item["descricao"]: item["id"] for item in data["types"]}
    with st.form("customer_ticket_form", clear_on_submit=True):
        selected_type = st.selectbox(
            "Tipo do chamado",
            list(type_options),
            key="customer_ticket_type",
        )
        description = st.text_area(
            "Descrição",
            placeholder="Descreva a ocorrência e o local.",
            height=130,
            key="customer_ticket_description",
        )
        photos = st.file_uploader(
            "Fotos do chamado",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            max_upload_size=10,
            key="customer_ticket_photos",
        ) or []
        submitted = st.form_submit_button(
            "Enviar chamado",
            type="primary",
            width="stretch",
        )

    if submitted:
        if not description.strip():
            st.error("Informe uma descrição para o chamado.")
        elif len(photos) > 5:
            st.error("Anexe no máximo 5 fotos por chamado.")
        else:
            ticket_id = data["next_ticket_id"]
            data["tickets"].append(
                {
                    "id": ticket_id,
                    "cliente_id": client["id"],
                    "tipo_id": type_options[selected_type],
                    "data_abertura": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "data_fechamento": "",
                    "canal_entrada": "Portal",
                    "status": "Chamados abertos",
                    "descricao": description.strip(),
                    "notificar_whatsapp": False,
                    "notificar_email": False,
                    "fotos": [
                        {"nome": photo.name, "conteudo": photo.getvalue()}
                        for photo in photos
                    ],
                    "materiais_utilizados": [],
                }
            )
            data["next_ticket_id"] += 1
            st.session_state.customer_navigation = "Chamados"
            st.session_state.flash_success = f"Chamado #{ticket_id} enviado para a equipe."
            st.rerun()

    if st.button("Cancelar", key="customer_ticket_cancel"):
        st.session_state.customer_navigation = "Chamados"
        st.rerun()


def render_customer_portal():
    client = next(
        (
            item
            for item in st.session_state.data["clients"]
            if item["id"] == st.session_state.get("client_id")
        ),
        None,
    )
    if client is None:
        st.error("Não foi possível localizar o cadastro vinculado a esta conta. Entre novamente.")
        if st.button("Voltar para o login", key="customer_missing_profile_logout"):
            logout_user()
        return

    st.session_state.setdefault("customer_navigation", "Chamados")
    if "flash_success" in st.session_state:
        st.success(st.session_state.pop("flash_success"))
    selected_module = st.session_state.customer_navigation
    if selected_module == "Novo chamado":
        page_title(
            "ÁREA DO CLIENTE",
            "Novo chamado",
            "Envie uma solicitação para a equipe da Defesa Civil.",
        )
        render_customer_ticket_form(client)
    else:
        page_title(
            "ÁREA DO CLIENTE",
            "Chamados",
            f"Acompanhe suas solicitações, {client['nome']}.",
        )
        st.markdown(
            '<div class="section-heading"><div><h2>Meus chamados</h2>'
            '<p>Somente as solicitações vinculadas ao seu cadastro são exibidas.</p></div></div>',
            unsafe_allow_html=True,
        )
        tickets = sorted(
            (
                ticket
                for ticket in st.session_state.data["tickets"]
                if ticket["cliente_id"] == client["id"]
            ),
            key=ticket_opened_datetime,
            reverse=True,
        )
        if tickets:
            for ticket in tickets:
                render_ticket_card(ticket)
        else:
            st.info("Você ainda não possui chamados. Use “Abrir chamado” para enviar uma solicitação.")


def render_dashboard():
    data = st.session_state.data
    page_title(
        "VISÃO GERAL",
        "Central de atendimento",
        "Acompanhe as ocorrências e atualizações da equipe em um só lugar.",
        "＋ Novo chamado",
        "Novo chamado",
    )
    tickets = data["tickets"]

    captions = {
        "Chamados abertos": "Aguardando atendimento",
        "Em andamento": "Em atendimento pela equipe",
        "Aguardando retorno": "Dependem de uma resposta",
        "Finalizado": "Solicitações resolvidas",
    }
    columns = st.columns(4)
    for column, status in zip(columns, STATUSES):
        presentation = status_presentation(status)
        total = sum(ticket["status"] == status for ticket in tickets)
        with column:
            with st.container(border=True, key=f"dashboard-metric-{presentation['class']}"):
                st.badge(
                    presentation["label"],
                    icon=f":material/{presentation['icon']}:",
                    color=presentation["color"],
                )
                st.metric(presentation["label"], total, label_visibility="collapsed")
                st.caption(captions[status])

    st.markdown(
        '<div class="section-heading"><div><h2>Distribuição dos chamados</h2>'
        '<p>Volumes e percentuais por fase e classificação dos chamados em aberto</p></div></div>',
        unsafe_allow_html=True,
    )
    chart_columns = st.columns(2)
    with chart_columns[0]:
        with st.container(border=True, key="dashboard-chart-status"):
            st.markdown("**Chamados por fase**")
            st.metric("Total geral de chamados", len(tickets))
            status_counts = Counter(ticket["status"] for ticket in tickets)
            status_data = [
                {
                    "fase": status_presentation(status)["label"],
                    "quantidade": status_counts[status],
                    "percentual": (
                        100 * status_counts[status] / len(tickets) if tickets else 0
                    ),
                }
                for status in STATUSES
            ]
            status_chart = horizontal_bar_chart(
                status_data,
                "fase",
                "Fase",
                STATUS_COLORS,
            )
            st.altair_chart(
                status_chart,
                alt="Chamados por fase, com quantidade e percentual do total geral",
                width="stretch",
            )

    with chart_columns[1]:
        with st.container(border=True, key="dashboard-chart-classification"):
            st.markdown("**Classificações em aberto**")
            open_by_type = Counter(
                type_name(ticket["tipo_id"])
                for ticket in tickets
                if ticket["status"] == "Chamados abertos"
            )
            open_total = sum(open_by_type.values())
            st.metric("Total de chamados em aberto", open_total)
            classification_data = [
                {
                    "classificacao": item_type["descricao"],
                    "quantidade": open_by_type[item_type["descricao"]],
                    "percentual": (
                        100 * open_by_type[item_type["descricao"]] / open_total
                        if open_total
                        else 0
                    ),
                }
                for item_type in data["types"]
            ]
            if classification_data:
                classification_chart = horizontal_bar_chart(
                    classification_data,
                    "classificacao",
                    "Classificação",
                    ["#E67817", "#29166F", "#6D28D9", "#15803D", "#1D4ED8"],
                )
                st.altair_chart(
                    classification_chart,
                    alt="Classificações dos chamados em aberto, com quantidade e percentual",
                    width="stretch",
                )
            else:
                st.info("Cadastre classificações para visualizar a distribuição.")

    st.markdown(
        '<div class="section-heading"><div><h2>Chamados recentes</h2>'
        '<p>Últimas solicitações registradas</p></div></div>',
        unsafe_allow_html=True,
    )
    recent = sorted(tickets, key=ticket_opened_datetime, reverse=True)[:3]
    if recent:
        for ticket in recent:
            render_ticket_card(ticket)
    else:
        st.markdown(
            '<div class="empty-state"><div class="empty-state-icon">◷</div>'
            '<div class="empty-state-title">Nenhum chamado cadastrado</div>'
            '<div class="empty-state-copy">Quando houver chamados, eles aparecerão aqui.</div></div>',
            unsafe_allow_html=True,
        )


def render_tickets():
    page_title(
        "ATENDIMENTO",
        "Chamados",
        "Acompanhe e atualize cada solicitação por fase.",
        "＋ Novo chamado",
        "Novo chamado",
    )
    filter_columns = st.columns([2, 1, 1.4])
    with filter_columns[0]:
        search = st.text_input(
            "Buscar chamado",
            placeholder="Número, solicitante ou descrição",
        )
    with filter_columns[1]:
        phase_filter = st.selectbox(
            "Fase",
            ["Todas"] + STATUSES,
            format_func=lambda status: (
                "Todas as fases"
                if status == "Todas"
                else status_presentation(status)["label"]
            ),
        )
    type_labels = sorted(
        {item_type["descricao"] for item_type in st.session_state.data["types"]},
        key=str.casefold,
    )
    with filter_columns[2]:
        classification_filter = st.selectbox(
            "Classificação",
            ["Todas"] + type_labels,
        )

    tickets = sorted(
        st.session_state.data["tickets"],
        key=ticket_opened_datetime,
        reverse=True,
    )
    filtered = [
        ticket
        for ticket in tickets
        if search.casefold()
        in f"{ticket['id']} {client_name(ticket['cliente_id'])} {ticket['descricao']}".casefold()
        and (phase_filter == "Todas" or ticket["status"] == phase_filter)
        and (
            classification_filter == "Todas"
            or type_name(ticket["tipo_id"]) == classification_filter
        )
    ]
    st.caption(f"{len(filtered)} chamado(s)")
    with st.container(key="kanban-board"):
        columns = st.columns(len(STATUSES))
        for column, status in zip(columns, STATUSES):
            phase = status_presentation(status)
            matching = [ticket for ticket in filtered if ticket["status"] == status]
            with column:
                st.markdown(
                    f'<div class="kanban-column-heading {phase["class"]}">'
                    f'<span>{phase["label"]}</span>'
                    f'<span class="kanban-count">{len(matching)}</span></div>',
                    unsafe_allow_html=True,
                )
                if matching:
                    for ticket in matching:
                        render_ticket_card(ticket, compact=True)
                else:
                    st.markdown(
                        '<div class="kanban-empty">Sem chamados nesta fase</div>',
                        unsafe_allow_html=True,
                    )
    if not filtered:
        st.info("Nenhum chamado corresponde aos filtros selecionados. Tente ajustar a busca ou os filtros.")


def render_new_ticket():
    page_title(
        "ATENDIMENTO",
        "Novo chamado",
        "Registre a solicitação, fotos e informações para contato.",
    )
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
        with second:
            status = st.selectbox("Fase inicial", STATUSES, index=0)
        type_column, channel_column = st.columns(2)
        with type_column:
            selected_type = st.selectbox("Tipo do chamado", list(type_options))
        with channel_column:
            channel = st.selectbox("Canal de entrada", CHANNELS)
        description = st.text_area(
            "Descrição",
            placeholder="Descreva a solicitação com o máximo de contexto possível.",
            height=130,
        )
        photos = st.file_uploader(
            "Fotos do chamado",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            max_upload_size=10,
        ) or []
        notify_whatsapp = st.checkbox("Notificar por WhatsApp")
        notify_email = st.checkbox("Notificar por e-mail")
        submitted = st.form_submit_button("Criar chamado", type="primary", width="stretch")
        if submitted:
            if not description.strip():
                st.error("Informe uma descrição para o chamado.")
            elif len(photos) > 5:
                st.error("Anexe no máximo 5 fotos por chamado.")
            else:
                ticket_id = data["next_ticket_id"]
                data["tickets"].append(
                    {
                        "id": ticket_id,
                        "cliente_id": client_options[selected_client],
                        "tipo_id": type_options[selected_type],
                        "data_abertura": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "data_fechamento": "",
                        "canal_entrada": channel,
                        "status": status,
                        "descricao": description.strip(),
                        "notificar_whatsapp": notify_whatsapp,
                        "notificar_email": notify_email,
                        "fotos": [
                            {"nome": photo.name, "conteudo": photo.getvalue()}
                            for photo in photos
                        ],
                        "materiais_utilizados": [],
                    }
                )
                data["next_ticket_id"] += 1
                st.success(f"Chamado #{ticket_id} criado.")
                st.session_state.navigation = "Chamados"
                st.rerun()


def render_clients():
    page_title("CADASTROS", "Clientes", "Gerencie os dados de contato e endereço dos clientes.")
    with st.expander("＋ Cadastrar cliente", expanded=False):
        with st.form("new_client_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nome completo")
                cpf = st.text_input("CPF")
                email = st.text_input("E-mail")
                whatsapp = st.text_input("WhatsApp")
            with col2:
                age = st.number_input("Idade", min_value=0, max_value=120, value=18)
                state = st.text_input("Estado (UF)", max_chars=2)
                cep = st.text_input("CEP", max_chars=9)
                neighborhood = st.text_input("Bairro")
            street = st.text_input("Rua")
            reference = st.text_input("Ponto de referência")
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
                            "cep": cep.strip(),
                            "bairro": neighborhood.strip(),
                            "rua": street.strip(),
                            "ponto_referencia": reference.strip(),
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
            address = " · ".join(
                value
                for value in [
                    client.get("rua", ""),
                    client.get("bairro", ""),
                    client.get("cep", ""),
                    client.get("ponto_referencia", ""),
                ]
                if value
            )
            st.caption(f"Endereço: {address or 'Não informado'}")


def render_types():
    page_title("CONFIGURAÇÕES", "Tipos de chamado", "Organize as solicitações por categoria.")
    with st.form("new_type_form", clear_on_submit=True):
        description = st.text_input("Descrição do tipo", placeholder="Ex.: Alagamento")
        submitted = st.form_submit_button("＋ Adicionar tipo", type="primary")
        if submitted:
            if not description.strip():
                st.error("Informe a descrição do tipo.")
            elif any(
                item["descricao"].casefold() == description.strip().casefold()
                for item in st.session_state.data["types"]
            ):
                st.error("Este tipo já está cadastrado.")
            else:
                types = st.session_state.data["types"]
                types.append(
                    {
                        "id": max((item["id"] for item in types), default=0) + 1,
                        "descricao": description.strip(),
                    }
                )
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


def render_materials():
    page_title("CADASTROS", "Materiais", "Cadastre materiais e seus valores unitários para usar no fechamento.")
    with st.expander("＋ Cadastrar material", expanded=False):
        with st.form("new_material_form", clear_on_submit=True):
            description = st.text_input("Nome do material")
            value = st.number_input("Valor unitário (R$)", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            submitted = st.form_submit_button("Salvar material", type="primary")
            if submitted:
                if not description.strip():
                    st.error("Informe o nome do material.")
                elif any(
                    item["descricao"].casefold() == description.strip().casefold()
                    for item in st.session_state.data["materials"]
                ):
                    st.error("Este material já está cadastrado.")
                else:
                    materials = st.session_state.data["materials"]
                    materials.append(
                        {
                            "id": max((item["id"] for item in materials), default=0) + 1,
                            "descricao": description.strip(),
                            "valor": float(value),
                        }
                    )
                    st.success("Material cadastrado.")
                    st.rerun()

    materials = st.session_state.data["materials"]
    st.caption(f"{len(materials)} material(is) cadastrado(s)")
    if not materials:
        st.markdown(
            '<div class="empty-state"><div class="empty-state-icon">▦</div>'
            '<div class="empty-state-title">Nenhum material cadastrado</div>'
            '<div class="empty-state-copy">Cadastre materiais para registrá-los no encerramento dos chamados.</div></div>',
            unsafe_allow_html=True,
        )
    for material in materials:
        with st.container(border=True):
            name_col, value_col = st.columns([3, 1])
            with name_col:
                st.markdown(f"**{material['descricao']}**")
                st.caption(f"ID do material: {material['id']}")
            with value_col:
                st.metric("Valor unitário", f"R$ {material['valor']:.2f}".replace(".", ","))


def render_users():
    page_title("CONFIGURAÇÕES", "Usuários", "Visualize os acessos da equipe de atendimento.")
    users = st.session_state.data["users"]
    st.caption(f"{len(users)} usuário(s) cadastrado(s)")
    for user in users:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**{user['nome']}**")
                st.caption(user.get("email", "E-mail não informado"))
            with col2:
                st.write(user["permissao"])
                st.caption(f"ID do usuário: {user['id']}")
            with col3:
                st.markdown(status_badge(user["status"]), unsafe_allow_html=True)


st.set_page_config(
    page_title="Defesa Civil | Atendimento",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
setup_state()
apply_styles()

if not st.session_state.authenticated:
    render_login()
    st.stop()

if st.session_state.get("user_role") == "client":
    st.session_state.setdefault("customer_navigation", "Chamados")
    with st.sidebar:
        st.image(
            str(BASE_DIR / "assets" / "defesa_civil_concordia.jpeg"),
            width=90,
            alt="Logo da Defesa Civil de Concórdia, Santa Catarina",
        )
        st.markdown("### Área do Cliente")
        st.caption(st.session_state.get("user_name", "Cliente"))
        for module, icon in [
            ("Chamados", ":material/confirmation_number:"),
            ("Novo chamado", ":material/add_circle:"),
        ]:
            if st.button(
                module,
                icon=icon,
                key=f"customer_navigation_{module}",
                type=(
                    "primary"
                    if st.session_state.customer_navigation == module
                    else "secondary"
                ),
                width="stretch",
            ):
                st.session_state.customer_navigation = module
                st.rerun()
        if st.button("Sair", icon=":material/logout:", key="customer_logout"):
            logout_user()

    render_customer_portal()
    active_dialog = st.session_state.active_ticket_dialog
    if active_dialog and active_dialog[0] == "details":
        ticket = find_ticket(active_dialog[1])
        if ticket and ticket["cliente_id"] == st.session_state.get("client_id"):
            show_ticket_details(active_dialog[1])
        else:
            st.error("Este chamado não pertence ao seu cadastro.")
            st.session_state.active_ticket_dialog = None
    st.stop()

with st.sidebar:
    with st.container(key="sidebar-layout"):
        st.image(
            str(BASE_DIR / "assets" / "defesa_civil_concordia.jpeg"),
            width=90,
            alt="Logo da Defesa Civil de Concórdia, Santa Catarina",
        )
        st.markdown(
            '<div class="brand"><div class="brand-name">Defesa Civil</div>'
            '<div class="brand-caption">CENTRAL DE ATENDIMENTO</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-label">MENU PRINCIPAL</div>', unsafe_allow_html=True)
        pages = [
            ("Visão geral", ":material/dashboard:"),
            ("Chamados", ":material/confirmation_number:"),
            ("Novo chamado", ":material/add_circle:"),
            ("Clientes", ":material/group:"),
            ("Materiais", ":material/inventory_2:"),
            ("Tipos", ":material/category:"),
            ("Usuários", ":material/manage_accounts:"),
        ]
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
            with st.popover(
                st.session_state.get("user_name", DEMO_USER),
                icon=":material/account_circle:",
                width="stretch",
            ):
                st.caption(st.session_state.get("user_name", DEMO_USER))
                st.caption(DEMO_EMAIL)
                if st.button(
                    "Sair",
                    icon=":material/logout:",
                    width="stretch",
                    key="sidebar_logout",
                ):
                    logout_user()
        selected_page = st.session_state.navigation

page_renderers = {
    "Visão geral": render_dashboard,
    "Chamados": render_tickets,
    "Novo chamado": render_new_ticket,
    "Clientes": render_clients,
    "Materiais": render_materials,
    "Tipos": render_types,
    "Usuários": render_users,
}
if "flash_success" in st.session_state:
    st.success(st.session_state.pop("flash_success"))

page_renderers[selected_page]()
active_dialog = st.session_state.active_ticket_dialog
if active_dialog:
    dialog_type, ticket_id = active_dialog
    dialog_renderers = {
        "details": show_ticket_details,
        "phase": show_ticket_phase_dialog,
        "finish": show_ticket_finish_dialog,
    }
    dialog_renderer = dialog_renderers.get(dialog_type)
    if dialog_renderer:
        dialog_renderer(ticket_id)
