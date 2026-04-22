#!/bin/sh
set -e
python - <<'PY'
from run import app, db, _seed_if_empty
from app.utils.month_operation_sim import run_month_operation_simulation
with app.app_context():
    db.create_all()
    _seed_if_empty()
    run_month_operation_simulation()
PY
exec gunicorn -b 0.0.0.0:5001 --workers 2 run:app
