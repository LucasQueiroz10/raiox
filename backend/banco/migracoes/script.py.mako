"""${message}

Revisão: ${up_revision}
Anterior: ${down_revision | comma,n}
Criada em: ${create_date}
"""

from alembic import op

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    raise NotImplementedError("Migrações só vão para frente (ADR 0006): corrija com uma nova.")
