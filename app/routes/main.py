"""Public pages, trace-by-code, health check."""
from flask import jsonify, redirect, render_template, url_for
from sqlalchemy import text

from app import db
from app.models import WasteBatch, WasteStatusHistory


def register_routes(app):
    @app.route('/')
    def index():
        # Always show project landing (SDG 12 blurb, features, grader box). Logged-in users
        # get a banner with a link to the dashboard instead of being redirected away.
        return render_template('index.html')

    @app.route('/trace/<string:code>')
    def trace_batch(code):
        batch = WasteBatch.query.filter(
            (WasteBatch.trace_code == code) | (WasteBatch.batch_code == code)
        ).first_or_404()
        history = (
            WasteStatusHistory.query.filter_by(waste_batch_id=batch.id)
            .order_by(WasteStatusHistory.changed_at.asc())
            .all()
        )
        return render_template('trace.html', batch=batch, history=history)

    @app.route('/cover')
    def project_cover():
        """Same landing as home (cover-style UI); kept for old links."""
        return redirect(url_for('index'))

    @app.route('/health')
    def health():
        try:
            db.session.execute(text('SELECT 1'))
        except Exception as e:
            return jsonify({'status': 'unhealthy', 'database': str(e)}), 503
        return jsonify({'status': 'ok', 'service': 'hazwaste-management'})
