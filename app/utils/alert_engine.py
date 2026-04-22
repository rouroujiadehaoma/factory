"""Rule evaluation → AlertEvent records (idempotent per batch+rule+message hash)."""
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func

from app import db
from app.models import AlertEvent, AlertRule, WasteBatch
from config import Config


def _dedupe_key(rule_id: int, batch_id: int, message: str) -> str:
    raw = f"{rule_id}:{batch_id}:{message}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _open_event_exists(rule_id: int, batch_id: int, message: str) -> bool:
    q = AlertEvent.query.filter_by(
        rule_id=rule_id,
        waste_batch_id=batch_id,
        message=message,
        status='open',
    )
    return db.session.query(q.exists()).scalar()


def evaluate_rules_for_batch(
    batch: WasteBatch,
    rules: List[AlertRule],
    *,
    now: Optional[datetime] = None,
) -> int:
    """Create new open AlertEvents where appropriate. Returns count of new events."""
    created = 0
    now = now or datetime.utcnow()
    for rule in rules:
        if not rule.enabled:
            continue
        severity = rule.severity or 'info'
        msg = None

        if rule.rule_type == 'storage_exceeds_days':
            try:
                days = int(rule.threshold or 0)
            except (TypeError, ValueError):
                continue
            if batch.current_status in ('registered', 'stored', 'pending_transfer'):
                age = now - (batch.created_at or now)
                if age > timedelta(days=days):
                    msg = (
                        f'Batch {batch.batch_code} stored/overdue beyond {days} days '
                        f'(status={batch.current_status}).'
                    )

        elif rule.rule_type == 'hazard_minimum_level':
            order = {h: i for i, h in enumerate(Config.HAZARD_LEVELS)}
            try:
                min_idx = order.get(str(rule.threshold).lower(), -1)
            except Exception:
                min_idx = -1
            if min_idx >= 0 and batch.hazard_level:
                if order.get(batch.hazard_level, -1) >= min_idx:
                    msg = (
                        f'Batch {batch.batch_code} hazard level {batch.hazard_level} '
                        f'meets/exceeds rule threshold {rule.threshold}.'
                    )

        elif rule.rule_type == 'remark_keyword':
            keywords = [k.strip().lower() for k in str(rule.threshold or '').split(',') if k.strip()]
            text = (batch.remarks or '').lower()
            hit = next((k for k in keywords if k in text), None)
            if hit:
                msg = f'Batch {batch.batch_code} remark contains flagged keyword "{hit}".'

        elif rule.rule_type == 'location_capacity':
            try:
                cap = float(rule.threshold)
            except (TypeError, ValueError):
                continue
            loc = batch.storage_location or ''
            if not loc:
                continue
            total_qty = (
                db.session.query(func.coalesce(func.sum(WasteBatch.quantity), 0.0))
                .filter(
                    WasteBatch.storage_location == loc,
                    WasteBatch.current_status.notin_(('disposed', 'archived')),
                )
                .scalar()
            )
            if float(total_qty or 0) > cap:
                msg = (
                    f'Storage location "{loc}" aggregate quantity {total_qty} '
                    f'exceeds threshold {cap}.'
                )

        elif rule.rule_type == 'inactive_batch_days':
            try:
                days = int(rule.threshold or 0)
            except (TypeError, ValueError):
                continue
            if batch.current_status in ('registered', 'stored'):
                last = batch.updated_at or batch.created_at or now
                if (now - last) > timedelta(days=days):
                    msg = (
                        f'Batch {batch.batch_code} inactive for over {days} days '
                        f'while status={batch.current_status}.'
                    )

        if msg:
            if rule.rule_type == 'location_capacity':
                dup = AlertEvent.query.filter_by(rule_id=rule.id, message=msg, status='open').first()
            else:
                dup = _open_event_exists(rule.id, batch.id, msg)
            if dup:
                continue
            ev = AlertEvent(
                rule_id=rule.id,
                waste_batch_id=batch.id,
                severity=severity,
                message=msg,
                status='open',
                dedupe_key=_dedupe_key(rule.id, batch.id, msg),
                created_at=now,
            )
            db.session.add(ev)
            created += 1
    return created


def run_full_evaluation(*, now: Optional[datetime] = None) -> int:
    """Evaluate all enabled rules against all non-archived batches."""
    rules = AlertRule.query.filter_by(enabled=True).all()
    batches = WasteBatch.query.filter(WasteBatch.current_status != 'archived').all()
    total = 0
    eval_now = now or datetime.utcnow()
    for b in batches:
        total += evaluate_rules_for_batch(b, rules, now=eval_now)
    db.session.commit()
    return total
