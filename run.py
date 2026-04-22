"""Run development server, init DB, seed roles & demo data."""
from app import create_app, db
from app.models import AlertRule, User, WasteBatch
from app.utils.month_operation_sim import run_month_operation_simulation

app = create_app()


def _seed_if_empty():
    if User.query.first():
        return
    users = [
        ('admin', 'admin@plant.example', 'administrator', 'Admin123!'),
        ('es_officer', 'eso@plant.example', 'es_officer', 'Eso123!'),
        ('operator1', 'op@plant.example', 'operator', 'Op123!'),
        ('auditor1', 'audit@plant.example', 'auditor', 'Audit123!'),
    ]
    for username, email, role, pwd in users:
        u = User(username=username, email=email, role=role, status='active')
        u.set_password(pwd)
        db.session.add(u)
    db.session.commit()

    rules = [
        ('Long storage — 60d', 'storage_exceeds_days', '60', 'warning'),
        ('High hazard watch', 'hazard_minimum_level', 'high', 'critical'),
        ('Remark keywords', 'remark_keyword', 'leak,spill,fire', 'critical'),
        ('Tank farm capacity (kg)', 'location_capacity', '50000', 'warning'),
        ('Stale registered batch', 'inactive_batch_days', '30', 'info'),
    ]
    for name, rtype, thr, sev in rules:
        db.session.add(
            AlertRule(
                rule_name=name,
                rule_type=rtype,
                threshold=thr,
                severity=sev,
                enabled=1,
            )
        )
    db.session.commit()


@app.shell_context_processor
def shell_ctx():
    from app.models import AlertEvent, AlertRule, AuditLog, User, WasteBatch

    return {
        'db': db,
        'User': User,
        'WasteBatch': WasteBatch,
        'AlertRule': AlertRule,
        'AlertEvent': AlertEvent,
        'AuditLog': AuditLog,
    }


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        _seed_if_empty()
        run_month_operation_simulation()
    app.run(debug=True, host='0.0.0.0', port=5001)
