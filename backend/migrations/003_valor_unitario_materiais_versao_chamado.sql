-- 003_valor_unitario_materiais_versao_chamado.sql

-- Adiciona valor_unitario histórico aos materiais do chamado
ALTER TABLE chamado_materiais
ADD COLUMN IF NOT EXISTS valor_unitario NUMERIC(10,2) NOT NULL DEFAULT 0.00;

-- Atualiza registros existentes com o valor atual do catálogo como fallback inicial
UPDATE chamado_materiais cm
SET valor_unitario = m.valor
FROM materiais m
WHERE cm.material_id = m.id_material AND cm.valor_unitario = 0.00;

-- Adiciona controle de versão ao chamado para evitar conflito concorrente de edição
ALTER TABLE chamados
ADD COLUMN IF NOT EXISTS versao INTEGER NOT NULL DEFAULT 1;
