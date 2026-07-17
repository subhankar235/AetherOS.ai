"""add google integrations

Revision ID: e6d5b77c128f
Revises: d3b14e11a743
Create Date: 2026-07-16 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e6d5b77c128f'
down_revision: Union[str, Sequence[str], None] = 'd3b14e11a743'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create google_integrations table
    op.create_table(
        'google_integrations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scopes', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_google_integrations_user_id'), 'google_integrations', ['user_id'], unique=True)

    # 2. Enable RLS and create tenant isolation policy
    op.execute("ALTER TABLE google_integrations ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY google_integrations_isolation_policy ON google_integrations "
        "FOR ALL USING (user_id = current_setting('app.current_user_id', true)::uuid) "
        "WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid);"
    )


def downgrade() -> None:
    # 1. Drop RLS isolation policy
    op.execute("DROP POLICY IF EXISTS google_integrations_isolation_policy ON google_integrations;")
    
    # 2. Drop google_integrations table
    op.drop_index(op.f('ix_google_integrations_user_id'), table_name='google_integrations')
    op.drop_table('google_integrations')
