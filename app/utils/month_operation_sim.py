"""
Day-by-day operational simulation (~one calendar month).

Uses the same paths as live operations: legal state transitions, audit logging,
transfer records when entering transit, periodic alert rule evaluation, and
occasional report / ERP sync records. Timestamps are back-dated so dashboards
look like a plant that has been running for several weeks.

Idempotent: skips if a completion marker row exists in ``audit_log``.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from typing import List, Optional, Sequence

from app import db
from app.models import (
    AlertEvent,
    AlertRule,
    ExternalSyncRecord,
    ReportExportHistory,
    TransferRecord,
    User,
    WasteBatch,
    WasteStatusHistory,
)
from app.utils.alert_engine import evaluate_rules_for_batch, run_full_evaluation
from app.utils.audit_service import log_action
from app.utils.batch_util import next_batch_code
from app.utils.demo_timeline_seed import ensure_operator2
from app.utils.state_machine import can_transition, next_statuses
from config import Config

SIMULATION_MARKER_ENTITY = 'SimulationMarker'
SIMULATION_COMPLETE_ACTION = 'month_simulation_complete'
NUM_SIM_DAYS = 34
RNG_SEED = 20260422

NAMES = [
    'Spent MEK / toluene blend',
    'Caustic scrubber blowdown',
    'Ni catalyst fines',
    'Lab mixed organics',
    'Oily interceptor sludge',
    'Chlorinated tar residue',
    'HF neutralisation salts',
    'VOC adsorbent carbon',
]
CATEGORIES = [
    'organic_solvent',
    'aqueous',
    'catalyst',
    'lab_mixed',
    'oily_sludge',
    'chlorinated',
    'inorganic',
    'other',
]
LOCATIONS = [
    'Tank farm T-08',
    'Tank farm T-12',
    'Warehouse W-2',
    'Shed A-4',
    'Secure cage C-1',
    'Berm B-3',
]
UNITS_SRC = [
    'Unit-2 / Reforming',
    'Unit-3 / Alkylation',
    'Central laboratory',
    'Wastewater treatment',
]
VENDORS = [
    'GreenDisposal Ltd',
    'Atlantic Hazmat Hauling',
    'ChemCycle EU',
]


def _simulation_done() -> bool:
    from app.models import AuditLog

    return (
        db.session.query(AuditLog.id)
        .filter_by(
            entity_type=SIMULATION_MARKER_ENTITY,
            action=SIMULATION_COMPLETE_ACTION,
        )
        .limit(1)
        .first()
        is not None
    )


def _pick_operator(operators: Sequence[User], rng: random.Random) -> User:
    return operators[rng.randrange(0, len(operators))]


def _sole_next_status(current: str) -> Optional[str]:
    choices = sorted(next_statuses(current))
    if not choices:
        return None
    return choices[0]


def sim_create_batch(
    actor: User,
    *,
    name: str,
    category: str,
    source_unit: str,
    quantity: float,
    unit: str,
    storage_location: str,
    hazard_level: str,
    responsible_person: str,
    remarks: Optional[str],
    is_abnormal: int,
    created_at: datetime,
) -> WasteBatch:
    code = next_batch_code()
    batch = WasteBatch(
        batch_code=code,
        trace_code=code,
        name=name,
        category=category,
        source_unit=source_unit,
        quantity=quantity,
        unit=unit,
        storage_location=storage_location,
        hazard_level=hazard_level,
        responsible_person=responsible_person,
        current_status='registered',
        remarks=remarks,
        is_abnormal=is_abnormal,
        external_disposal_info=None,
        created_by=actor.id,
        created_at=created_at,
        updated_at=created_at,
    )
    db.session.add(batch)
    db.session.flush()
    db.session.add(
        WasteStatusHistory(
            waste_batch_id=batch.id,
            from_status=None,
            to_status='registered',
            changed_by=actor.id,
            comment='Registration (simulated shift)',
            changed_at=created_at,
        )
    )
    log_action(
        actor=actor,
        entity_type='WasteBatch',
        entity_id=batch.id,
        action='create',
        before=None,
        after={
            'batch_code': batch.batch_code,
            'status': batch.current_status,
            'name': batch.name,
        },
        created_at=created_at,
    )
    return batch


def sim_transition(
    actor: User,
    batch: WasteBatch,
    to_status: str,
    comment: str,
    at: datetime,
    rng: random.Random,
) -> None:
    if not can_transition(batch.current_status, to_status):
        return
    before_status = batch.current_status
    batch.current_status = to_status
    batch.updated_at = at
    db.session.add(
        WasteStatusHistory(
            waste_batch_id=batch.id,
            from_status=before_status,
            to_status=to_status,
            changed_by=actor.id,
            comment=comment,
            changed_at=at,
        )
    )
    log_action(
        actor=actor,
        entity_type='WasteBatch',
        entity_id=batch.id,
        action='status_transition',
        before={'status': before_status},
        after={'status': to_status},
        remark=comment,
        created_at=at,
    )
    if to_status == 'in_transit':
        tr_at = at + timedelta(hours=1, minutes=rng.randint(5, 55))
        rec = TransferRecord(
            waste_batch_id=batch.id,
            transfer_vendor=VENDORS[rng.randrange(len(VENDORS))],
            transfer_time=tr_at,
            destination='Regional TSDF — licensed cell',
            manifest_number=f'HW-MNF-{batch.id:06d}',
            received_status='in_transit',
        )
        db.session.add(rec)
        log_action(
            actor=actor,
            entity_type='TransferRecord',
            entity_id=batch.id,
            action='transfer_recorded',
            after={'vendor': rec.transfer_vendor, 'manifest': rec.manifest_number},
            created_at=tr_at,
        )


def sim_maybe_edit_batch(actor: User, batch: WasteBatch, at: datetime, rng: random.Random) -> None:
    if batch.current_status in ('disposed', 'archived'):
        return
    if rng.random() > 0.12:
        return
    before = {
        'quantity': batch.quantity,
        'remarks': batch.remarks,
    }
    delta = round(rng.uniform(-3.0, 3.0), 2)
    batch.quantity = max(1.0, round(batch.quantity + delta, 2))
    if rng.random() < 0.25:
        batch.remarks = (batch.remarks or '') + ' Field recount verified.'
    batch.updated_at = at
    log_action(
        actor=actor,
        entity_type='WasteBatch',
        entity_id=batch.id,
        action='update',
        before=before,
        after={'quantity': batch.quantity, 'remarks': batch.remarks},
        created_at=at,
    )


def _resolve_some_open_alerts(es_officer: User, at: datetime, rng: random.Random) -> None:
    open_ev: List[AlertEvent] = (
        AlertEvent.query.filter_by(status='open').order_by(AlertEvent.id).limit(25).all()
    )
    rng.shuffle(open_ev)
    for ev in open_ev[: max(1, len(open_ev) // 3)]:
        ev.status = 'resolved'
        ev.acknowledged_at = at - timedelta(hours=2)
        ev.resolved_at = at
        ev.resolution_note = 'Closed after simulated EHS review.'
        log_action(
            actor=es_officer,
            entity_type='AlertEvent',
            entity_id=ev.id,
            action='alert_resolved',
            after={'rule_id': ev.rule_id, 'batch_id': ev.waste_batch_id},
            created_at=at,
        )


def _seed_legacy_drums(
    operators: Sequence[User],
    sim_start: datetime,
    rng: random.Random,
) -> None:
    """Two drums already on site (triggers long-storage rule once simulated clock catches up)."""
    for i in range(2):
        actor = _pick_operator(operators, rng)
        t0 = sim_start - timedelta(days=72 + i * 3)
        remarks = 'Legacy drum from turnaround — hold for profiling.' if i == 0 else None
        b = sim_create_batch(
            actor,
            name=f'Legacy hold drum {i + 1}',
            category='organic_solvent',
            source_unit='Tank farm operations',
            quantity=float(800 + i * 120),
            unit='kg',
            storage_location='Tank farm T-12',
            hazard_level='high',
            responsible_person=actor.username,
            remarks=remarks,
            is_abnormal=0,
            created_at=t0,
        )
        t1 = t0 + timedelta(hours=6)
        sim_transition(actor, b, 'stored', 'Moved to bunded storage (backfill)', t1, rng)


def run_month_operation_simulation() -> None:
    """Run after ``_seed_if_empty`` (users + alert rules). Safe to call on every startup."""
    if not User.query.first():
        return
    if _simulation_done():
        return

    ensure_operator2()
    rng = random.Random(RNG_SEED)

    operators = User.query.filter_by(role=Config.ROLE_OPERATOR).order_by(User.id).all()
    es_officer = User.query.filter_by(role=Config.ROLE_ES_OFFICER).first()
    admin = User.query.filter_by(role=Config.ROLE_ADMINISTRATOR).first()
    if not operators or not es_officer:
        return

    sim_start = datetime.utcnow().replace(hour=6, minute=0, second=0, microsecond=0) - timedelta(
        days=NUM_SIM_DAYS
    )

    rules = AlertRule.query.filter_by(enabled=True).all()

    _seed_legacy_drums(operators, sim_start, rng)
    db.session.commit()

    for day in range(NUM_SIM_DAYS):
        day_base = sim_start + timedelta(days=day)
        creates = rng.choices([1, 2, 2, 3, 3, 4], weights=[1, 2, 3, 3, 2, 1], k=1)[0]

        for _ in range(creates):
            actor = _pick_operator(operators, rng)
            t_reg = day_base + timedelta(hours=rng.uniform(6.0, 11.5))
            qty = round(rng.uniform(12.0, 480.0), 1)
            hazard = rng.choices(
                Config.HAZARD_LEVELS,
                weights=[30, 28, 25, 17],
                k=1,
            )[0]
            remark = None
            if rng.random() < 0.06:
                remark = 'Minor weep noted at flange — containment OK.'
            if rng.random() < 0.04:
                remark = 'Suspected leak during transfer; isolated.'

            sim_create_batch(
                actor,
                name=f'{rng.choice(NAMES)} (sim lot {day}-{rng.randint(10, 99)})',
                category=rng.choice(CATEGORIES),
                source_unit=rng.choice(UNITS_SRC),
                quantity=qty,
                unit=rng.choice(['kg', 'L', 'ton']),
                storage_location=rng.choice(LOCATIONS),
                hazard_level=hazard,
                responsible_person=actor.username,
                remarks=remark,
                is_abnormal=1 if remark and 'leak' in remark.lower() else 0,
                created_at=t_reg,
            )

        # Intra-day status movements (several waves)
        for wave in range(3):
            wave_t = day_base + timedelta(hours=12 + wave * 4)
            batches = WasteBatch.query.filter(WasteBatch.current_status != 'archived').all()
            rng.shuffle(batches)
            for batch in batches:
                age_days = (wave_t - (batch.created_at or wave_t)).total_seconds() / 86400.0
                p_move = min(0.82, 0.12 + max(0.0, age_days) * 0.035 + wave * 0.07)
                if rng.random() > p_move:
                    continue
                nxt = _sole_next_status(batch.current_status)
                if not nxt:
                    continue
                actor = _pick_operator(operators, rng)
                comments = [
                    'Shift handover',
                    'EHS checkpoint cleared',
                    'Carrier slot confirmed',
                    'Weighbridge OK',
                    'TSDF receipt logged',
                ]
                sim_transition(actor, batch, nxt, rng.choice(comments), wave_t, rng)

        # Field edits (quantity / remarks)
        edit_time = day_base + timedelta(hours=rng.uniform(14.0, 18.0))
        for batch in WasteBatch.query.filter(WasteBatch.current_status != 'archived').limit(80).all():
            sim_maybe_edit_batch(_pick_operator(operators, rng), batch, edit_time, rng)

        # End-of-day rule pass (same engine as dashboard button)
        eod = day_base.replace(hour=22, minute=30)
        batches_live = WasteBatch.query.filter(WasteBatch.current_status != 'archived').all()
        for b in batches_live:
            evaluate_rules_for_batch(b, rules, now=eod)
        db.session.commit()

        # EHS clears part of the alert queue (simulated triage)
        _resolve_some_open_alerts(es_officer, eod + timedelta(minutes=45), rng)

        # Weekly reporting / integration noise
        if day % 7 == 2 and admin:
            db.session.add(
                ReportExportHistory(
                    exported_by=admin.id,
                    report_type='summary_csv' if day % 14 == 2 else 'monthly_pdf',
                    file_path='simulation',
                    created_at=eod,
                )
            )
            log_action(
                actor=admin,
                entity_type='ReportExportHistory',
                entity_id=day,
                action='report_export',
                after={'report_type': 'summary_csv' if day % 14 == 2 else 'monthly_pdf'},
                created_at=eod,
            )
        if day % 5 == 0:
            db.session.add(
                ExternalSyncRecord(
                    source_system=rng.choice(['ERP', 'LIMS']),
                    direction=rng.choice(['inbound', 'outbound']),
                    payload=json.dumps(
                        {'sim_day': day, 'posted_at': eod.isoformat(), 'plant': 'DEMO-1'}
                    ),
                    status='received',
                    created_at=eod - timedelta(minutes=20),
                )
            )

        db.session.commit()

    # Final evaluation at "today"
    run_full_evaluation(now=datetime.utcnow())

    marker_actor = admin or es_officer
    log_action(
        actor=marker_actor,
        entity_type=SIMULATION_MARKER_ENTITY,
        entity_id=0,
        action=SIMULATION_COMPLETE_ACTION,
        after={'sim_days': NUM_SIM_DAYS, 'seed': RNG_SEED},
        remark='Synthetic month completed; startup will not re-run unless marker removed.',
        created_at=datetime.utcnow(),
    )
    db.session.commit()
