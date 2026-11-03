CREATE TABLE usuarios (
    id_usuario INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    permissao VARCHAR(50) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    status boolean default true,
    nome VARCHAR(255) NOT NULL
);

CREATE TABLE clientes (
    id_cliente INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cidade VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    email VARCHAR(150),
    status boolean default true,
    whatsapp VARCHAR(20)
);

CREATE TABLE tipos (
    id_tipo INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    descricao VARCHAR(255) NOT NULL
);

CREATE TABLE chamados (
    id_chamado INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    canal_entrada VARCHAR(50) NOT NULL
        CHECK (canal_entrada IN (
            'WhatsApp',
            'E-mail',
            'Portal',
            'Presencialmente'
        )),
    descricao TEXT NOT NULL,
    status VARCHAR(100) NOT NULL
        CHECK (status IN (
            'Em aberto',
            'Em andamento',
            'Aguardando retorno',
            'Finalizado'
        )),
    data_abertura TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_limite TIMESTAMP,
    data_fechamento TIMESTAMP,
    notificar_email BOOLEAN NOT NULL DEFAULT FALSE,
    notificar_whatsapp BOOLEAN NOT NULL DEFAULT FALSE,
    cliente_id INTEGER NOT NULL,
    tipo_id INTEGER NOT NULL,

    CONSTRAINT fk_chamado_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id_cliente),

    CONSTRAINT fk_chamado_tipo
        FOREIGN KEY (tipo_id)
        REFERENCES tipos(id_tipo)
);