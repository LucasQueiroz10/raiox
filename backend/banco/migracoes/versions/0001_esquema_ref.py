"""Esquema ref e permissões de base do banco.

Revisão: 0001
Anterior: nenhuma
Criada em: 2026-10-07
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # O public fica sem uso e sem permissão para ninguém (ADR 0006, seção 2).
    op.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")

    # Só os usuários do projeto conectam ao banco, e só a ingestão cria tabelas temporárias, para a
    # preparação das cargas (seção 5). Sessões em UTC (seção 1).
    op.execute(
        """
        DO $$
        DECLARE
            banco text := current_database();
        BEGIN
            EXECUTE format('REVOKE ALL ON DATABASE %I FROM PUBLIC', banco);
            EXECUTE format('GRANT CONNECT ON DATABASE %I TO rx_api, rx_ingestao', banco);
            EXECUTE format('GRANT TEMPORARY ON DATABASE %I TO rx_ingestao', banco);
            EXECUTE format('ALTER DATABASE %I SET timezone TO %L', banco, 'UTC');
        END
        $$
        """
    )

    # Função nova não nasce executável por todos: o PostgreSQL dá EXECUTE a PUBLIC por padrão, e as
    # funções deste banco só valem para quem receber permissão (seção 6).
    op.execute("ALTER DEFAULT PRIVILEGES FOR ROLE rx_dono REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC")

    # Dados públicos de referência. A API e a ingestão enxergam o esquema; o que cada uma lê ou
    # grava vem com cada tabela ou visão.
    op.execute("CREATE SCHEMA ref")
    op.execute("GRANT USAGE ON SCHEMA ref TO rx_api, rx_ingestao")


def downgrade() -> None:
    raise NotImplementedError("Migrações só vão para frente (ADR 0006): corrija com uma nova.")
