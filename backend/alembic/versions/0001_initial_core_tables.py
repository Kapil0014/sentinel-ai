"""initial core tables

Revision ID: 0001
Revises: 
Create Date: 2026-11-19 12:59:58.817791
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('user', 'admin', name='user_role', native_enum=False, create_constraint=True, length=24), server_default='user', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index('uq_users_email_lower', 'users', [sa.literal_column('lower(email)')], unique=True)
    op.create_table('projects',
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_projects_owner_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_projects')),
    sa.UniqueConstraint('owner_id', 'name', name='uq_projects_owner_id_name')
    )
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)
    op.create_table('websites',
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('base_url', sa.String(length=2048), nullable=False),
    sa.Column('hostname', sa.String(length=255), nullable=False),
    sa.Column('allowed_domains', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    sa.Column('is_authorized_target', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_websites_project_id_projects'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_websites')),
    sa.UniqueConstraint('project_id', 'base_url', name='uq_websites_project_id_base_url')
    )
    op.create_index(op.f('ix_websites_project_id'), 'websites', ['project_id'], unique=False)
    op.create_table('testing_sessions',
    sa.Column('website_id', sa.UUID(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('mode', sa.Enum('autonomous', 'assisted', name='session_mode', native_enum=False, create_constraint=True, length=24), nullable=False),
    sa.Column('state', sa.Enum('CREATED', 'INITIALIZED', 'DISCOVERING', 'ANALYZING', 'GENERATING_TESTS', 'VALIDATING_TESTS', 'AWAITING_REVIEW', 'AWAITING_APPROVAL', 'EXECUTING', 'OBSERVING', 'REPORTING', 'COMPLETED', 'FAILED', 'CANCELLED', name='session_state', native_enum=False, create_constraint=True, length=24), server_default='CREATED', nullable=False),
    sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('cancel_requested', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_testing_sessions_created_by_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['website_id'], ['websites.id'], name=op.f('fk_testing_sessions_website_id_websites'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_testing_sessions'))
    )
    op.create_index(op.f('ix_testing_sessions_created_by'), 'testing_sessions', ['created_by'], unique=False)
    op.create_index('ix_testing_sessions_state', 'testing_sessions', ['state'], unique=False)
    op.create_index('ix_testing_sessions_website_id_created_at', 'testing_sessions', ['website_id', sa.literal_column('created_at DESC')], unique=False)


def downgrade() -> None:
    op.drop_index('ix_testing_sessions_website_id_created_at', table_name='testing_sessions')
    op.drop_index('ix_testing_sessions_state', table_name='testing_sessions')
    op.drop_index(op.f('ix_testing_sessions_created_by'), table_name='testing_sessions')
    op.drop_table('testing_sessions')
    op.drop_index(op.f('ix_websites_project_id'), table_name='websites')
    op.drop_table('websites')
    op.drop_index(op.f('ix_projects_owner_id'), table_name='projects')
    op.drop_table('projects')
    op.drop_index('uq_users_email_lower', table_name='users')
    op.drop_table('users')
