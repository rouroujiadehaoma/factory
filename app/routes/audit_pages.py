"""Audit log viewer (administrator, ES officer, operator, auditor)."""
from flask import render_template, request
from flask_login import login_required
from sqlalchemy import and_

from app.forms import AuditFilterForm
from app.models import AuditLog
from app.utils.rbac import roles_required
from config import Config


def register_routes(app):
    viewers = (
        Config.ROLE_ADMINISTRATOR,
        Config.ROLE_ES_OFFICER,
        Config.ROLE_OPERATOR,
        Config.ROLE_AUDITOR,
    )

    @app.route('/audit/logs')
    @login_required
    @roles_required(*viewers)
    def audit_logs():
        form = AuditFilterForm(request.args)
        q = AuditLog.query
        if form.actor.data:
            q = q.filter(AuditLog.actor_name.ilike(f'%{form.actor.data}%'))
        if form.entity_type.data:
            q = q.filter(AuditLog.entity_type.ilike(f'%{form.entity_type.data}%'))
        if form.batch_id.data:
            try:
                bid = int(form.batch_id.data)
                q = q.filter(and_(AuditLog.entity_type == 'WasteBatch', AuditLog.entity_id == bid))
            except ValueError:
                pass
        page = request.args.get('page', 1, type=int)
        pagination = q.order_by(AuditLog.created_at.desc()).paginate(
            page=page, per_page=Config.POSTS_PER_PAGE, error_out=False
        )
        return render_template('audit/logs.html', pagination=pagination, form=form)
