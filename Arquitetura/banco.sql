CREATE TABLE usuarios (
    id_usuario INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    permissao VARCHAR(50) NOT NULL,
    status BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE clientes (
    id_cliente INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(150),
    whatsapp VARCHAR(20),
    cep VARCHAR(9),
    rua VARCHAR(255),
    bairro VARCHAR(100),
    cidade VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    ponto_referencia VARCHAR(255),
    status BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE cliente_contas (
    id_conta INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_id INTEGER NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR NOT NULL,
    CONSTRAINT fk_cliente_conta_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id_cliente)
        ON DELETE CASCADE
);

CREATE TABLE tipos (
    id_tipo INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    descricao VARCHAR(255) NOT NULL
);

CREATE TABLE chamados (
    id_chamado INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    descricao TEXT NOT NULL,

    canal_entrada VARCHAR(50) NOT NULL
        CHECK (
            canal_entrada IN (
                'WhatsApp',
                'E-mail',
                'Telefone',
                'Portal',
                'Presencialmente'
            )
        ),

    status VARCHAR(100) NOT NULL DEFAULT 'Em aberto'
        CHECK (
            status IN (
                'Em aberto',
                'Em andamento',
                'Aguardando retorno',
                'Finalizado'
            )
        ),

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

CREATE INDEX ix_chamados_cliente_abertura
    ON chamados (cliente_id, data_abertura DESC);
CREATE INDEX ix_chamados_status_abertura
    ON chamados (status, data_abertura DESC);
CREATE INDEX ix_chamados_tipo_id
    ON chamados (tipo_id);

CREATE TABLE chamado_fotos (
    id_foto INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chamado_id INTEGER NOT NULL,
    caminho_foto VARCHAR(500) NOT NULL,
    data_upload TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_foto_chamado
        FOREIGN KEY (chamado_id)
        REFERENCES chamados(id_chamado)
        ON DELETE CASCADE
);

CREATE TABLE materiais (
    id_material INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    descricao VARCHAR(255) NOT NULL,
    unidade_medida VARCHAR(50) NOT NULL,
    valor NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    status BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE chamado_materiais (
    id_chamado_material INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chamado_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantidade NUMERIC(10,2) NOT NULL
        CHECK (quantidade > 0),

    CONSTRAINT fk_chamado_material_chamado
        FOREIGN KEY (chamado_id)
        REFERENCES chamados(id_chamado)
        ON DELETE CASCADE,

    CONSTRAINT fk_chamado_material_material
        FOREIGN KEY (material_id)
        REFERENCES materiais(id_material),

    CONSTRAINT uq_chamado_material
        UNIQUE (chamado_id, material_id)
);