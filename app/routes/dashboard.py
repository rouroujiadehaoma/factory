"""Executive dashboard + chart payloads."""
from collections import defaultdict
from datetime import datetime, timedelta

from flask import jsonify, render_template
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.models import AlertEvent, WasteBatch
from app.forms import RunAlertEvalForm
from app.utils.alert_engine import run_full_evaluation
from app.utils.rbac import roles_required
from config import Config


def _stats_payload():
    now = datetime.utcnow()
    total_batches = WasteBatch.query.count()
    total_weight = db.session.query(func.coalesce(func.sum(WasteBatch.quantity), 0.0)).scalar() or 0.0

    by_status = dict(
        db.session.query(WasteBatch.current_status, func.count(WasteBatch.id))
        .group_by(WasteBatch.current_status)
        .all()
    )
    by_category = dict(
        db.session.query(WasteBatch.category, func.count(WasteBatch.id))
        .group_by(WasteBatch.category)
        .all()
    )
    high_hazard = WasteBatch.query.filter(WasteBatch.hazard_level.in_(('high', 'critical'))).count()
    high_ratio = (high_hazard / total_batches) if total_batches else 0.0

    open_alerts = AlertEvent.query.filter_by(status='open').count()

    # Last ~6 months creation trend (Python bucket — works on SQLite and MySQL)
    trend = defaultdict(int)
    start = (now.replace(day=1) - timedelta(days=180)).replace(day=1)
    recent = WasteBatch.query.filter(WasteBatch.created_at >= start).all()
    for b in recent:
        if b.created_at:
            trend[b.created_at.strftime('%Y-%m')] += 1
    trend_labels = sorted(trend.keys())
    trend_values = [trend[k] for k in trend_labels]

    disposed = by_status.get('disposed', 0) + by_status.get('archived', 0)
    active = total_batches - by_status.get('archived', 0)
    disposal_rate = (disposed / active) if active else 0.0

    # Overdue heuristic: stored > 90 days
    cutoff = now - timedelta(days=90)
    overdue = WasteBatch.query.filter(
        WasteBatch.current_status.in_(('registered', 'stored', 'pending_transfer')),
        WasteBatch.created_at < cutoff,
    ).count()

    return {
        'total_batches': total_batches,
        'total_weight': float(total_weight),
        'by_status': by_status,
        'by_category': by_category,
        'open_alerts': open_alerts,
        'high_hazard_count': high_hazard,
        'high_hazard_ratio': round(high_ratio, 4),
        'trend_labels': trend_labels,
        'trend_values': trend_values,
        'disposal_rate': round(disposal_rate, 4),
        'overdue_batches': overdue,
    }


def register_routes(app):
    viewers = (
        Config.ROLE_ADMINISTRATOR,
        Config.ROLE_ES_OFFICER,
        Config.ROLE_OPERATOR,
        Config.ROLE_AUDITOR,
    )

    @app.route('/dashboard')
    @login_required
    @roles_required(*viewers)
    def dashboard():
        stats = _stats_payload()
        eval_form = RunAlertEvalForm()
        return render_template('dashboard.html', stats=stats, eval_form=eval_form)

    @app.route('/dashboard/stats.json')
    @login_required
    @roles_required(*viewers)
    def dashboard_stats_json():
        return jsonify(_stats_payload())

    @app.route('/dashboard/refresh-alerts', methods=['POST'])
    @login_required
    @roles_required(
        Config.ROLE_ADMINISTRATOR,
        Config.ROLE_ES_OFFICER,
    )
    def dashboard_refresh_alerts():
        n = run_full_evaluation()
        return jsonify({'evaluated_new_alerts': n})
