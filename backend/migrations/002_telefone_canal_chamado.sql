ALTER TABLE chamados
    DROP CONSTRAINT IF EXISTS chamados_canal_entrada_check;

ALTER TABLE chamados
    ADD CONSTRAINT chamados_canal_entrada_check
    CHECK (
        canal_entrada IN (
            'WhatsApp',
            'E-mail',
            'Telefone',
            'Portal',
            'Presencialmente'
        )
    );
