"""update_user_model_for_clerk

Revision ID: d3b14e11a743
Revises: 2e4684fe7803
Create Date: 2026-07-16 06:22:29.546254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3b14e11a743'
down_revision: Union[str, Sequence[str], None] = '2e4684fe7803'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop existing Foreign Key constraints first
    op.drop_constraint("agent_logs_user_id_fkey", "agent_logs", type_="foreignkey")
    op.drop_constraint("conversation_context_user_id_fkey", "conversation_context", type_="foreignkey")
    op.drop_constraint("drafts_user_id_fkey", "drafts", type_="foreignkey")
    op.drop_constraint("email_metadata_user_id_fkey", "email_metadata", type_="foreignkey")
    op.drop_constraint("knowledge_documents_user_id_fkey", "knowledge_documents", type_="foreignkey")
    op.drop_constraint("knowledge_documents_uploaded_by_fkey", "knowledge_documents", type_="foreignkey")
    op.drop_constraint("meetings_user_id_fkey", "meetings", type_="foreignkey")
    op.drop_constraint("payment_records_user_id_fkey", "payment_records", type_="foreignkey")
    op.drop_constraint("payment_records_approved_by_fkey", "payment_records", type_="foreignkey")
    op.drop_constraint("playbooks_user_id_fkey", "playbooks", type_="foreignkey")
    op.drop_constraint("purchase_orders_user_id_fkey", "purchase_orders", type_="foreignkey")
    op.drop_constraint("threads_user_id_fkey", "threads", type_="foreignkey")
    op.drop_constraint("vip_contacts_user_id_fkey", "vip_contacts", type_="foreignkey")

    # 2. Drop existing RLS policies that depend on user_id / id
    op.execute("DROP POLICY IF EXISTS users_isolation_policy ON users;")
    for table in ["email_metadata", "threads", "vip_contacts", "drafts", "meetings", "conversation_context", "agent_logs", "playbooks", "knowledge_documents", "purchase_orders", "payment_records"]:
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")

    # 3. Create the Enum type
    userrole = sa.Enum('OWNER', 'ADMIN', 'MEMBER', 'VIEWER', name='userrole')
    userrole.create(op.get_bind(), checkfirst=True)

    # 4. Alter columns from VARCHAR to UUID with proper casts
    op.alter_column('agent_logs', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=False,
               postgresql_using='user_id::uuid')
    op.alter_column('conversation_context', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=False,
               postgresql_using='user_id::uuid')
    op.alter_column('drafts', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=False,
               postgresql_using='user_id::uuid')
    op.alter_column('email_metadata', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=False,
               postgresql_using='user_id::uuid')
    op.alter_column('knowledge_documents', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=True,
               postgresql_using='user_id::uuid')
    op.alter_column('knowledge_documents', 'uploaded_by',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=True,
               postgresql_using='uploaded_by::uuid')
    op.alter_column('meetings', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=False,
               postgresql_using='user_id::uuid')
    op.alter_column('payment_records', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=True,
               postgresql_using='user_id::uuid')
    op.alter_column('payment_records', 'approved_by',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=True,
               postgresql_using='approved_by::uuid')
    op.alter_column('playbooks', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=True,
               postgresql_using='user_id::uuid')
    op.alter_column('purchase_orders', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=True,
               postgresql_using='user_id::uuid')
    op.alter_column('threads', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=False,
               postgresql_using='user_id::uuid')

    # Alter users table columns
    op.add_column('users', sa.Column('clerk_user_id', sa.String(), nullable=False))
    op.add_column('users', sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MEMBER', 'VIEWER', name='userrole'), nullable=False))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.alter_column('users', 'id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=False,
               postgresql_using='id::uuid')
    op.alter_column('users', 'timezone',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.create_index(op.f('ix_users_clerk_user_id'), 'users', ['clerk_user_id'], unique=True)
    op.drop_column('users', 'google_oauth_token')
    op.drop_column('users', 'oauth_scopes')

    op.alter_column('vip_contacts', 'user_id',
               existing_type=sa.VARCHAR(),
               type_=sa.UUID(),
               existing_nullable=False,
               postgresql_using='user_id::uuid')

    # 5. Re-create Foreign Key constraints referencing the new UUID users.id
    op.create_foreign_key("agent_logs_user_id_fkey", "agent_logs", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("conversation_context_user_id_fkey", "conversation_context", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("drafts_user_id_fkey", "drafts", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("email_metadata_user_id_fkey", "email_metadata", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("knowledge_documents_user_id_fkey", "knowledge_documents", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("knowledge_documents_uploaded_by_fkey", "knowledge_documents", "users", ["uploaded_by"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("meetings_user_id_fkey", "meetings", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("payment_records_user_id_fkey", "payment_records", "users", ["user_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("payment_records_approved_by_fkey", "payment_records", "users", ["approved_by"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("playbooks_user_id_fkey", "playbooks", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("purchase_orders_user_id_fkey", "purchase_orders", "users", ["user_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("threads_user_id_fkey", "threads", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("vip_contacts_user_id_fkey", "vip_contacts", "users", ["user_id"], ["id"], ondelete="CASCADE")

    # 6. Re-create RLS policies with UUID casts
    op.execute(
        "CREATE POLICY users_isolation_policy ON users "
        "FOR ALL USING (id = current_setting('app.current_user_id', true)::uuid) "
        "WITH CHECK (true);"
    )
    for table in ["email_metadata", "threads", "vip_contacts", "drafts", "meetings", "conversation_context", "agent_logs"]:
        op.execute(
            f"CREATE POLICY {table}_isolation_policy ON {table} "
            f"FOR ALL USING (user_id = current_setting('app.current_user_id', true)::uuid) "
            f"WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid);"
        )
    for table in ["playbooks", "knowledge_documents", "purchase_orders", "payment_records"]:
        op.execute(
            f"CREATE POLICY {table}_isolation_policy ON {table} "
            f"FOR ALL USING ("
            f"  user_id = current_setting('app.current_user_id', true)::uuid "
            f"  OR org_id = current_setting('app.current_org_id', true)"
            f") "
            f"WITH CHECK ("
            f"  user_id = current_setting('app.current_user_id', true)::uuid "
            f"  OR org_id = current_setting('app.current_org_id', true)"
            f");"
        )


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop UUID Foreign Keys
    op.drop_constraint("agent_logs_user_id_fkey", "agent_logs", type_="foreignkey")
    op.drop_constraint("conversation_context_user_id_fkey", "conversation_context", type_="foreignkey")
    op.drop_constraint("drafts_user_id_fkey", "drafts", type_="foreignkey")
    op.drop_constraint("email_metadata_user_id_fkey", "email_metadata", type_="foreignkey")
    op.drop_constraint("knowledge_documents_user_id_fkey", "knowledge_documents", type_="foreignkey")
    op.drop_constraint("knowledge_documents_uploaded_by_fkey", "knowledge_documents", type_="foreignkey")
    op.drop_constraint("meetings_user_id_fkey", "meetings", type_="foreignkey")
    op.drop_constraint("payment_records_user_id_fkey", "payment_records", type_="foreignkey")
    op.drop_constraint("payment_records_approved_by_fkey", "payment_records", type_="foreignkey")
    op.drop_constraint("playbooks_user_id_fkey", "playbooks", type_="foreignkey")
    op.drop_constraint("purchase_orders_user_id_fkey", "purchase_orders", type_="foreignkey")
    op.drop_constraint("threads_user_id_fkey", "threads", type_="foreignkey")
    op.drop_constraint("vip_contacts_user_id_fkey", "vip_contacts", type_="foreignkey")

    # 2. Drop existing RLS policies
    op.execute("DROP POLICY IF EXISTS users_isolation_policy ON users;")
    for table in ["email_metadata", "threads", "vip_contacts", "drafts", "meetings", "conversation_context", "agent_logs", "playbooks", "knowledge_documents", "purchase_orders", "payment_records"]:
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")

    # 3. Revert column types back to VARCHAR/String
    op.alter_column('vip_contacts', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using='user_id::varchar')
    op.add_column('users', sa.Column('oauth_scopes', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('google_oauth_token', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_users_clerk_user_id'), table_name='users')
    op.alter_column('users', 'timezone',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('users', 'id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using='id::varchar')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'role')
    op.drop_column('users', 'clerk_user_id')
    op.alter_column('threads', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using='user_id::varchar')
    op.alter_column('purchase_orders', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=True,
               postgresql_using='user_id::varchar')
    op.alter_column('playbooks', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=True,
               postgresql_using='user_id::varchar')
    op.alter_column('payment_records', 'approved_by',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=True,
               postgresql_using='approved_by::varchar')
    op.alter_column('payment_records', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=True,
               postgresql_using='user_id::varchar')
    op.alter_column('meetings', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using='user_id::varchar')
    op.alter_column('knowledge_documents', 'uploaded_by',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=True,
               postgresql_using='uploaded_by::varchar')
    op.alter_column('knowledge_documents', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=True,
               postgresql_using='user_id::varchar')
    op.alter_column('email_metadata', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using='user_id::varchar')
    op.alter_column('drafts', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using='user_id::varchar')
    op.alter_column('conversation_context', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using='user_id::varchar')
    op.alter_column('agent_logs', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using='user_id::varchar')

    # 4. Drop the Enum type
    userrole = sa.Enum('OWNER', 'ADMIN', 'MEMBER', 'VIEWER', name='userrole')
    userrole.drop(op.get_bind(), checkfirst=True)

    # 5. Re-create String Foreign Key constraints
    op.create_foreign_key("agent_logs_user_id_fkey", "agent_logs", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("conversation_context_user_id_fkey", "conversation_context", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("drafts_user_id_fkey", "drafts", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("email_metadata_user_id_fkey", "email_metadata", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("knowledge_documents_user_id_fkey", "knowledge_documents", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("knowledge_documents_uploaded_by_fkey", "knowledge_documents", "users", ["uploaded_by"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("meetings_user_id_fkey", "meetings", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("payment_records_user_id_fkey", "payment_records", "users", ["user_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("payment_records_approved_by_fkey", "payment_records", "users", ["approved_by"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("playbooks_user_id_fkey", "playbooks", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("purchase_orders_user_id_fkey", "purchase_orders", "users", ["user_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("threads_user_id_fkey", "threads", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("vip_contacts_user_id_fkey", "vip_contacts", "users", ["user_id"], ["id"], ondelete="CASCADE")

    # 6. Re-create original RLS policies (without UUID cast)
    op.execute(
        "CREATE POLICY users_isolation_policy ON users "
        "FOR ALL USING (id = current_setting('app.current_user_id', true)) "
        "WITH CHECK (true);"
    )
    for table in ["email_metadata", "threads", "vip_contacts", "drafts", "meetings", "conversation_context", "agent_logs"]:
        op.execute(
            f"CREATE POLICY {table}_isolation_policy ON {table} "
            f"FOR ALL USING (user_id = current_setting('app.current_user_id', true)) "
            f"WITH CHECK (user_id = current_setting('app.current_user_id', true));"
        )
    for table in ["playbooks", "knowledge_documents", "purchase_orders", "payment_records"]:
        op.execute(
            f"CREATE POLICY {table}_isolation_policy ON {table} "
            f"FOR ALL USING ("
            f"  user_id = current_setting('app.current_user_id', true) "
            f"  OR org_id = current_setting('app.current_org_id', true)"
            f") "
            f"WITH CHECK ("
            f"  user_id = current_setting('app.current_user_id', true) "
            f"  OR org_id = current_setting('app.current_org_id', true)"
            f");"
        )
