"""CNPJ alfanumérico nos formatos do banco; comentários do peso e dos temas vigentes.

Revisão: 0003
Anterior: 0002
Criada em: 2026-10-08
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Desde julho de 2026 a Receita Federal emite CNPJs com letras maiúsculas nos 12 primeiros
    # caracteres; os 2 dígitos verificadores continuam números e os CNPJs antigos continuam
    # valendo. O banco confere só o formato; o dígito verificador é conferido na aplicação
    # (app/core/identificadores.py). O formato novo aceita tudo o que o antigo aceitava.
    op.execute(
        r"""
        ALTER DOMAIN ref.ativo_id DROP CONSTRAINT ativo_id_check;
        ALTER DOMAIN ref.ativo_id ADD CONSTRAINT ativo_id_formato CHECK (
            VALUE ~ '^(BR|IE|LU|ZZ)[A-Z0-9]{9}[0-9]$'
            OR VALUE ~ '^US:[A-Z]{1,5}(\.[A-Z])?$'
            OR VALUE ~ '^CNPJ:[A-Z0-9]{12}[0-9]{2}$'
        );

        ALTER DOMAIN ref.empresa_id DROP CONSTRAINT empresa_id_check;
        ALTER DOMAIN ref.empresa_id ADD CONSTRAINT empresa_id_formato CHECK (
            VALUE ~ '^BR:CNPJ:[A-Z0-9]{12}[0-9]{2}$'
            OR VALUE ~ '^US:CIK:[0-9]{10}$'
            OR VALUE ~ '^LEI:[A-Z0-9]{18}[0-9]{2}$'
            OR VALUE ~ '^ZZ:[A-Z0-9]{1,20}$'
        );

        ALTER TABLE ref.empresa
            DROP CONSTRAINT empresa_cnpj_check,
            ADD CONSTRAINT empresa_cnpj_formato CHECK (cnpj ~ '^[A-Z0-9]{12}[0-9]{2}$');
        """
    )

    # Regras da 0002 explicadas no próprio banco.
    op.execute(
        """
        COMMENT ON COLUMN ref.composicao_item.peso IS
            'Fração do patrimônio do fundo, calculada na carga. Pode ser negativa: venda a '
            'descoberto, derivativo com valor de mercado negativo, caixa e valores a pagar.';

        COMMENT ON VIEW ref.classificacao_tema_vigente IS
            'Temas aprovados só de empresas com setor aprovado. Sem setor aprovado a empresa '
            'fica sem classificação, porque a parte que não é tema (o núcleo) é do setor.';
        """
    )


def downgrade() -> None:
    raise NotImplementedError("Migrações só vão para frente (ADR 0006): corrija com uma nova.")
