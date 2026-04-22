"""Append-only style audit logging for compliance."""
import json
from datetime import datetime
from typing import Any, Optional

from app import db
from app.models import AuditLog


def _serialize(data: Any) -> Optional[str]:
    if data is None:
        return None
    try:
        return json.dumps(data, default=str, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(data), ensure_ascii=False)


def log_action(
    *,
    actor,
    entity_type: str,
    entity_id: int,
    action: str,
    before: Any = None,
    after: Any = None,
    remark: Optional[str] = None,
    created_at: Optional[datetime] = None,
) -> None:
    """Persist one audit row (call within an active db.session transaction)."""
    entry = AuditLog(
        actor_id=actor.id if actor and getattr(actor, 'id', None) else None,
        actor_name=getattr(actor, 'username', None) or 'system',
        actor_role=getattr(actor, 'role', None) or 'system',
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_data=_serialize(before),
        after_data=_serialize(after),
        remark=remark,
        created_at=created_at or datetime.utcnow(),
    )
    db.session.add(entry)


def log_action_commit(**kwargs) -> None:
    log_action(**kwargs)
    db.session.commit()
