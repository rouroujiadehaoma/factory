"""Domain models: hazardous waste batches, RBAC users, audit, alerts, transfers."""
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'cp_user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, disabled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    batches_created = db.relationship(
        'WasteBatch', backref='creator', lazy='dynamic', foreign_keys='WasteBatch.created_by'
    )

    def get_id(self):
        return str(self.id)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_auditor(self) -> bool:
        return self.role == 'auditor'

    def is_operator(self) -> bool:
        return self.role == 'operator'

    def is_es_officer(self) -> bool:
        return self.role == 'es_officer'

    def is_administrator(self) -> bool:
        return self.role == 'administrator'


class WasteBatch(db.Model):
    __tablename__ = 'waste_batch'

    id = db.Column(db.Integer, primary_key=True)
    batch_code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    source_unit = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0.0)
    unit = db.Column(db.String(32), nullable=False, default='kg')
    storage_location = db.Column(db.String(120), nullable=False)
    hazard_level = db.Column(db.String(32), nullable=False, default='low')
    responsible_person = db.Column(db.String(120), nullable=False)
    current_status = db.Column(db.String(64), nullable=False, default='registered')
    remarks = db.Column(db.Text)
    is_abnormal = db.Column(db.Integer, default=0)
    external_disposal_info = db.Column(db.Text)
    trace_code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('cp_user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    status_history = db.relationship('WasteStatusHistory', backref='batch', lazy='dynamic')
    transfers = db.relationship('TransferRecord', backref='batch', lazy='dynamic')
    alert_events = db.relationship('AlertEvent', backref='batch', lazy='dynamic')


class WasteStatusHistory(db.Model):
    __tablename__ = 'waste_status_history'

    id = db.Column(db.Integer, primary_key=True)
    waste_batch_id = db.Column(db.Integer, db.ForeignKey('waste_batch.id'), nullable=False, index=True)
    from_status = db.Column(db.String(64))
    to_status = db.Column(db.String(64), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('cp_user.id'), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    comment = db.Column(db.Text)

    actor = db.relationship('User', foreign_keys=[changed_by])


class TransferRecord(db.Model):
    __tablename__ = 'transfer_record'

    id = db.Column(db.Integer, primary_key=True)
    waste_batch_id = db.Column(db.Integer, db.ForeignKey('waste_batch.id'), nullable=False, index=True)
    transfer_vendor = db.Column(db.String(200), nullable=False)
    transfer_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    destination = db.Column(db.String(300))
    manifest_number = db.Column(db.String(120))
    received_status = db.Column(db.String(64))


class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('cp_user.id'), index=True)
    actor_name = db.Column(db.String(80))
    actor_role = db.Column(db.String(32))
    entity_type = db.Column(db.String(64), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    action = db.Column(db.String(64), nullable=False)
    before_data = db.Column(db.Text)
    after_data = db.Column(db.Text)
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class AlertRule(db.Model):
    __tablename__ = 'alert_rule'

    id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(120), nullable=False)
    rule_type = db.Column(db.String(64), nullable=False)
    threshold = db.Column(db.String(255))
    severity = db.Column(db.String(32), default='warning')
    enabled = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AlertEvent(db.Model):
    __tablename__ = 'alert_event'

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('alert_rule.id'), index=True)
    waste_batch_id = db.Column(db.Integer, db.ForeignKey('waste_batch.id'), index=True)
    severity = db.Column(db.String(32), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), default='open')  # open, acknowledged, resolved
    dedupe_key = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    resolution_note = db.Column(db.Text)

    rule = db.relationship('AlertRule', backref='events')


class ReportExportHistory(db.Model):
    __tablename__ = 'report_export_history'

    id = db.Column(db.Integer, primary_key=True)
    exported_by = db.Column(db.Integer, db.ForeignKey('cp_user.id'), nullable=False)
    report_type = db.Column(db.String(64), nullable=False)
    file_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExternalSyncRecord(db.Model):
    __tablename__ = 'external_sync_record'

    id = db.Column(db.Integer, primary_key=True)
    source_system = db.Column(db.String(64), nullable=False)
    direction = db.Column(db.String(32), nullable=False)  # inbound, outbound
    payload = db.Column(db.Text)
    status = db.Column(db.String(32), default='received')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
