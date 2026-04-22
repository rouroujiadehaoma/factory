import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Chemical Plant Hazardous Waste Management System — configuration."""

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-change-me-hazwaste-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        'sqlite:///' + os.path.join(basedir, 'hazard_waste.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    POSTS_PER_PAGE = 20

    # External integration mock
    EXTERNAL_API_KEY = os.environ.get('EXTERNAL_API_KEY') or 'demo-hazwaste-api-key'

    LOG_DIR = os.path.join(basedir, 'logs')

    # Lifecycle states (order matters for display)
    WASTE_STATUSES = [
        'registered',
        'stored',
        'pending_transfer',
        'in_transit',
        'received_by_disposal_vendor',
        'disposed',
        'archived',
    ]

    HAZARD_LEVELS = ['low', 'medium', 'high', 'critical']

    ROLE_ADMINISTRATOR = 'administrator'
    ROLE_ES_OFFICER = 'es_officer'
    ROLE_OPERATOR = 'operator'
    ROLE_AUDITOR = 'auditor'

    ROLES = [
        ROLE_ADMINISTRATOR,
        ROLE_ES_OFFICER,
        ROLE_OPERATOR,
        ROLE_AUDITOR,
    ]

    # Optional invite codes on self-registration (empty → operator). Admin accounts should be created by an administrator.
    REGISTRATION_INVITE_ES = os.environ.get('REGISTRATION_INVITE_ES') or 'UCD-ES-2026'
    REGISTRATION_INVITE_AUDITOR = os.environ.get('REGISTRATION_INVITE_AUDITOR') or 'UCD-AUDIT-2026'
