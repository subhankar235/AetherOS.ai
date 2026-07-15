"""enable rls

Revision ID: 16aeb1f0d329
Revises: 6c7d8a89fe52
Create Date: 2026-07-15 23:56:41.249620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16aeb1f0d329'
down_revision: Union[str, Sequence[str], None] = '6c7d8a89fe52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # List of tables to enable RLS and add basic policy checking user_id
    user_scoped_tables = [
        "email_metadata", "threads", "vip_contacts", "drafts", 
        "meetings", "conversation_context", "agent_logs"
    ]
    
    user_or_org_scoped_tables = [
        "playbooks", "knowledge_documents", "purchase_orders", "payment_records"
    ]
    
    org_scoped_tables = [
        "vendors", "payment_policies"
    ]
    
    # 1. users table RLS
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY users_isolation_policy ON users "
        "FOR ALL USING (id = current_setting('app.current_user_id', true)) "
        "WITH CHECK (true);"
    )
    
    # 2. user-scoped tables RLS
    for table in user_scoped_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY {table}_isolation_policy ON {table} "
            f"FOR ALL USING (user_id = current_setting('app.current_user_id', true)) "
            f"WITH CHECK (user_id = current_setting('app.current_user_id', true));"
        )
        
    # 3. user-or-org-scoped tables RLS
    for table in user_or_org_scoped_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
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
        
    # 4. org-scoped tables RLS
    for table in org_scoped_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY {table}_isolation_policy ON {table} "
            f"FOR ALL USING (org_id = current_setting('app.current_org_id', true)) "
            f"WITH CHECK (org_id = current_setting('app.current_org_id', true));"
        )


def downgrade() -> None:
    # List of all tables
    tables = [
        "users", "email_metadata", "threads", "vip_contacts", "playbooks", 
        "knowledge_documents", "drafts", "meetings", "conversation_context", 
        "agent_logs", "purchase_orders", "payment_records", "vendors", "payment_policies"
    ]
    
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS users_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
