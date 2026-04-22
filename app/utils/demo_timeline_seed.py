"""Shared demo helpers (extra operator account for multi-user traces)."""

from app import db
from app.models import User
from config import Config


def ensure_operator2():
    if User.query.filter_by(username='operator2').first():
        return
    u = User(
        username='operator2',
        email='operator2@plant.example',
        role=Config.ROLE_OPERATOR,
        status='active',
    )
    u.set_password('Op123!')
    db.session.add(u)
    db.session.commit()
