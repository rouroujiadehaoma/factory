"""Batch code / trace code generation."""
from datetime import datetime

from sqlalchemy import func

from app import db
from app.models import WasteBatch


def next_batch_code() -> str:
    year = datetime.utcnow().year
    prefix = f'HW-{year}-'
    n = (
        db.session.query(func.count(WasteBatch.id))
        .filter(WasteBatch.batch_code.like(f'{prefix}%'))
        .scalar()
        or 0
    )
    seq = int(n) + 1
    return f'{prefix}{seq:05d}'
