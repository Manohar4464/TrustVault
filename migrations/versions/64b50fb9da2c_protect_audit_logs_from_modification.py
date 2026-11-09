
"""protect audit logs from modification

Revision ID: 64b50fb9da2c
Revises: 58d43aeb87d7
"""

from typing import Sequence, Union

from alembic import op

revision: str = "64b50fb9da2c"
down_revision: Union[str, Sequence[str], None] = "58d43aeb87d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a PostgreSQL trigger function.
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'Audit logs are immutable: UPDATE and DELETE are prohibited';
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Prevent UPDATE operations.
    op.execute("""
        CREATE TRIGGER trg_prevent_audit_log_update
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_modification();
    """)

    # Prevent DELETE operations.
    op.execute("""
        CREATE TRIGGER trg_prevent_audit_log_delete
        BEFORE DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_modification();
    """)


def downgrade() -> None:
    # Remove triggers before removing their function.
    op.execute("""
        DROP TRIGGER IF EXISTS trg_prevent_audit_log_update
        ON audit_logs;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS trg_prevent_audit_log_delete
        ON audit_logs;
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS prevent_audit_log_modification();
    """)
