"""Alert center: list, acknowledge, resolve, rule evaluation."""
from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import AlertResolveForm, RunAlertEvalForm
from app.models import AlertEvent
from app.utils.alert_engine import run_full_evaluation
from app.utils.rbac import roles_required
from config import Config


def register_routes(app):
    viewers = (
        Config.ROLE_ADMINISTRATOR,
        Config.ROLE_ES_OFFICER,
        Config.ROLE_OPERATOR,
        Config.ROLE_AUDITOR,
    )
    resolvers = (Config.ROLE_ADMINISTRATOR, Config.ROLE_ES_OFFICER)

    @app.route('/alerts')
    @login_required
    @roles_required(*viewers)
    def alert_list():
        status = request.args.get('status', 'open')
        q = AlertEvent.query
        if status in ('open', 'acknowledged', 'resolved'):
            q = q.filter_by(status=status)
        elif status != 'all':
            q = q.filter_by(status='open')
        events = q.order_by(AlertEvent.created_at.desc()).limit(200).all()
        return render_template('alerts/list.html', events=events, filter_status=status)

    @app.route('/alerts/<int:event_id>/ack', methods=['POST'])
    @login_required
    @roles_required(*resolvers)
    def alert_ack(event_id):
        ev = AlertEvent.query.get_or_404(event_id)
        if ev.status == 'open':
            ev.status = 'acknowledged'
            ev.acknowledged_at = datetime.utcnow()
            db.session.commit()
            flash('Alert acknowledged.', 'info')
        return redirect(url_for('alert_list'))

    @app.route('/alerts/<int:event_id>/resolve', methods=['GET', 'POST'])
    @login_required
    @roles_required(*resolvers)
    def alert_resolve(event_id):
        ev = AlertEvent.query.get_or_404(event_id)
        form = AlertResolveForm()
        if form.validate_on_submit():
            ev.status = 'resolved'
            ev.resolved_at = datetime.utcnow()
            ev.resolution_note = form.resolution_note.data
            db.session.commit()
            flash('Alert resolved.', 'success')
            return redirect(url_for('alert_list'))
        return render_template('alerts/resolve.html', form=form, event=ev)

    @app.route('/alerts/run-evaluation', methods=['POST'])
    @login_required
    @roles_required(Config.ROLE_ADMINISTRATOR, Config.ROLE_ES_OFFICER)
    def alert_run_evaluation():
        form = RunAlertEvalForm()
        if not form.validate_on_submit():
            flash('Invalid request.', 'danger')
            return redirect(url_for('dashboard'))
        n = run_full_evaluation()
        flash(f'Evaluation complete. New alerts: {n}.', 'success')
        return redirect(url_for('alert_list'))
