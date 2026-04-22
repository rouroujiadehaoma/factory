"""Administrator: user provisioning, alert rule configuration."""
from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import AlertRuleForm, UserAdminForm
from app.models import AlertRule, User
from app.utils.audit_service import log_action
from app.utils.rbac import roles_required
from config import Config


def register_routes(app):
    @app.route('/admin/users')
    @login_required
    @roles_required(Config.ROLE_ADMINISTRATOR)
    def admin_users():
        users = User.query.order_by(User.id).all()
        return render_template('admin/users.html', users=users)

    @app.route('/admin/users/new', methods=['GET', 'POST'])
    @login_required
    @roles_required(Config.ROLE_ADMINISTRATOR)
    def admin_user_new():
        form = UserAdminForm()
        if form.validate_on_submit():
            if User.query.filter_by(username=form.username.data).first():
                flash('Username exists.', 'danger')
            elif User.query.filter_by(email=form.email.data).first():
                flash('Email exists.', 'danger')
            else:
                u = User(
                    username=form.username.data,
                    email=form.email.data,
                    role=form.role.data,
                    status='active',
                )
                u.set_password(form.password.data)
                db.session.add(u)
                db.session.flush()
                log_action(
                    actor=current_user,
                    entity_type='User',
                    entity_id=u.id,
                    action='create_user',
                    after={'username': u.username, 'role': u.role},
                )
                db.session.commit()
                flash('User created.', 'success')
                return redirect(url_for('admin_users'))
        return render_template('admin/user_form.html', form=form)

    @app.route('/admin/rules')
    @login_required
    @roles_required(Config.ROLE_ADMINISTRATOR)
    def admin_rules():
        rules = AlertRule.query.order_by(AlertRule.id).all()
        form = AlertRuleForm()
        return render_template('admin/rules.html', rules=rules, form=form)

    @app.route('/admin/rules/new', methods=['POST'])
    @login_required
    @roles_required(Config.ROLE_ADMINISTRATOR)
    def admin_rule_new():
        form = AlertRuleForm()
        if form.validate_on_submit():
            r = AlertRule(
                rule_name=form.rule_name.data,
                rule_type=form.rule_type.data,
                threshold=form.threshold.data,
                severity=form.severity.data,
                enabled=1 if form.enabled.data else 0,
            )
            db.session.add(r)
            log_action(
                actor=current_user,
                entity_type='AlertRule',
                entity_id=0,
                action='create_rule',
                after={'name': r.rule_name, 'type': r.rule_type},
            )
            db.session.commit()
            flash('Rule saved.', 'success')
        else:
            flash('Invalid rule form.', 'danger')
        return redirect(url_for('admin_rules'))

    @app.route('/admin/rules/<int:rule_id>/toggle', methods=['POST'])
    @login_required
    @roles_required(Config.ROLE_ADMINISTRATOR)
    def admin_rule_toggle(rule_id):
        r = AlertRule.query.get_or_404(rule_id)
        r.enabled = 0 if r.enabled else 1
        db.session.commit()
        flash('Rule updated.', 'info')
        return redirect(url_for('admin_rules'))
