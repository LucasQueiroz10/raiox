"""Código interno da B3, ticker com número na raiz e o tipo dos FIIs na identificação.

Revisão: 0004
Anterior: 0003
Criada em: 2026-10-13
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Código interno para ação sem ISIN conhecido (ADR 0005, seção 5; decisão de 13/10/2026):
    # "B3:" + ticker. Vale para as ações que nenhum fundo tem: só o CDA traz o ISIN junto do
    # ticker, e o FCA, que liga o ticker à companhia, não traz ISIN. A raiz do ticker (4
    # caracteres) é o código do emissor na B3 e começa sempre por letra (B3SA3 tem número no meio).
    op.execute(
        r"""
        ALTER DOMAIN ref.ativo_id DROP CONSTRAINT ativo_id_formato;
        ALTER DOMAIN ref.ativo_id ADD CONSTRAINT ativo_id_formato CHECK (
            VALUE ~ '^(BR|IE|LU|ZZ)[A-Z0-9]{9}[0-9]$'
            OR VALUE ~ '^US:[A-Z]{1,5}(\.[A-Z])?$'
            OR VALUE ~ '^CNPJ:[A-Z0-9]{12}[0-9]{2}$'
            OR VALUE ~ '^B3:[A-Z][A-Z0-9]{3}[0-9]{1,2}$'
        );

        ALTER TABLE ref.ativo
            DROP CONSTRAINT ativo_ticker_b3_check,
            ADD CONSTRAINT ativo_ticker_b3_formato
                CHECK (ticker_b3 ~ '^[A-Z][A-Z0-9]{3}[0-9]{1,2}$'),
            ADD CONSTRAINT codigo_b3_so_em_acao
                CHECK (ativo_id::text NOT LIKE 'B3:%' OR tipo = 'acao');
        """
    )

    # Tipo de cada FII (ADR 0008, etapa 4; regra em ingest/cvm_fii.py), calculado na carga a partir
    # do informe mensal de FII da CVM. O segmento só existe no tijolo; sem ele, vários segmentos.
    op.execute(
        """
        ALTER TABLE ref.ativo
            ADD COLUMN fii_tipo text
                CHECK (fii_tipo IN ('tijolo', 'papel', 'fundo_de_fundos', 'generico')),
            ADD COLUMN fii_segmento text,
            ADD CONSTRAINT fii_so_em_fundo CHECK (fii_tipo IS NULL OR tipo = 'fundo'),
            -- IS NOT DISTINCT FROM: com fii_tipo vazio, "= 'tijolo'" daria NULL e passaria.
            ADD CONSTRAINT segmento_so_em_tijolo
                CHECK (fii_segmento IS NULL OR fii_tipo IS NOT DISTINCT FROM 'tijolo');

        COMMENT ON COLUMN ref.ativo.fii_tipo IS
            'Tipo do FII pela carteira do informe mensal da CVM: o grupo com mais da metade do '
            'investido (tijolo, papel ou fundo de fundos); sem grupo dominante, genérico.';
        COMMENT ON COLUMN ref.ativo.fii_segmento IS
            'Segmento declarado pelo FII, só no tijolo; vazio: vários segmentos.';

        -- As colunas novas entram no fim da visão (CREATE OR REPLACE mantém as permissões).
        CREATE OR REPLACE VIEW ref.ativo_vigente AS
        SELECT a.ativo_id, a.tipo, a.empresa_id, a.ticker_b3, a.ticker_eua, a.isin, a.nome,
            a.aproximado_por, a.fii_tipo, a.fii_segmento
        FROM ref.ativo a
        JOIN ref.foto_vigente f ON f.tipo = 'identificacao' AND f.carga_id = a.carga_id;
        """
    )


def downgrade() -> None:
    raise NotImplementedError("Migrações só vão para frente (ADR 0006): corrija com uma nova.")
