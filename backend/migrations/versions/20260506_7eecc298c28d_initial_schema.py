"""initial schema

Revision ID: 7eecc298c28d
Revises:
Create Date: 2026-05-06 22:45:06.917189
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7eecc298c28d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ENUM types (PostgreSQL) ───────────────────────────────────────────────
    userrole_enum = sa.Enum('patient', 'doctor', 'admin', name='userrole')
    userrole_enum.create(op.get_bind(), checkfirst=True)

    reportstatus_enum = sa.Enum('processing', 'done', 'error', name='reportstatus')
    reportstatus_enum.create(op.get_bind(), checkfirst=True)

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('patient', 'doctor', 'admin', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # ── patients ──────────────────────────────────────────────────────────────
    op.create_table(
        'patients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('medical_history', sa.Text(), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.Column('current_medications', sa.Text(), nullable=True),
        sa.Column('emergency_contact', sa.String(255), nullable=True),
    )
    op.create_index('ix_patients_user_id', 'patients', ['user_id'], unique=True)

    # ── vitals ────────────────────────────────────────────────────────────────
    op.create_table(
        'vitals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('heart_rate', sa.Integer(), nullable=True),
        sa.Column('blood_pressure_systolic', sa.Integer(), nullable=True),
        sa.Column('blood_pressure_diastolic', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('oxygen_saturation', sa.Float(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('anomaly_detected', sa.Boolean(), nullable=False),
        sa.Column('anomaly_score', sa.Float(), nullable=True),
    )
    op.create_index('ix_vitals_patient_id', 'vitals', ['patient_id'])
    op.create_index('ix_vitals_patient_timestamp', 'vitals', ['patient_id', 'created_at'])

    # ── chat_history ──────────────────────────────────────────────────────────
    op.create_table(
        'chat_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('ai_response', sa.Text(), nullable=False),
        sa.Column('agent_used', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False),
        sa.Column('feedback', sa.String(10), nullable=True),
        sa.Column('feedback_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_chat_history_patient_id', 'chat_history', ['patient_id'])

    # ── medical_reports ───────────────────────────────────────────────────────
    op.create_table(
        'medical_reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('status', sa.Enum('processing', 'done', 'error', name='reportstatus'), nullable=False),
        sa.Column('faiss_doc_id', sa.Integer(), nullable=True),
        sa.Column('text_preview', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
    )
    op.create_index('ix_medical_reports_patient_id', 'medical_reports', ['patient_id'])

    # ── medications ───────────────────────────────────────────────────────────
    op.create_table(
        'medications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('medication_name', sa.String(255), nullable=False),
        sa.Column('dosage', sa.String(100), nullable=False),
        sa.Column('frequency', sa.String(100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
    )
    op.create_index('ix_medications_patient_id', 'medications', ['patient_id'])
    op.create_index('ix_medications_patient_startdate', 'medications', ['patient_id', 'start_date'])

    # ── doctor_messages ───────────────────────────────────────────────────────
    op.create_table(
        'doctor_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('doctor_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('sender_role', sa.String(10), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
    )
    op.create_index('ix_doctor_messages_patient_id', 'doctor_messages', ['patient_id'])
    op.create_index('ix_doctor_messages_doctor_user_id', 'doctor_messages', ['doctor_user_id'])

    # ── appointments ──────────────────────────────────────────────────────────
    op.create_table(
        'appointments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('doctor_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('preferred_date', sa.String(20), nullable=True),
        sa.Column('preferred_time_slot', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('doctor_notes', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.String(50), nullable=True),
        sa.Column('ai_suggested', sa.Boolean(), nullable=False),
        sa.Column('attachment_path', sa.String(500), nullable=True),
    )
    op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'])
    op.create_index('ix_appointments_doctor_user_id', 'appointments', ['doctor_user_id'])

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('user_role', sa.String(50), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('outcome', sa.String(20), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_user_created', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('ix_audit_action_created', 'audit_logs', ['action', 'created_at'])

    # ── doctor_patient_assignments ────────────────────────────────────────────
    op.create_table(
        'doctor_patient_assignments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('doctor_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('assigned_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.UniqueConstraint('doctor_user_id', 'patient_id', name='uq_doctor_patient'),
    )
    op.create_index('ix_dpa_doctor_user_id', 'doctor_patient_assignments', ['doctor_user_id'])
    op.create_index('ix_dpa_patient_id', 'doctor_patient_assignments', ['patient_id'])


def downgrade() -> None:
    # Drop in reverse FK order
    op.drop_table('doctor_patient_assignments')
    op.drop_table('audit_logs')
    op.drop_table('appointments')
    op.drop_table('doctor_messages')
    op.drop_table('medications')
    op.drop_table('medical_reports')
    op.drop_table('chat_history')
    op.drop_table('vitals')
    op.drop_table('patients')
    op.drop_table('users')
    # Drop ENUM types after all tables that reference them are gone
    sa.Enum(name='reportstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
