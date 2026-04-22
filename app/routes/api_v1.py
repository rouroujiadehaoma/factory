"""REST API for external integration (API key) + mock inbound sync."""
import json
from datetime import datetime

from flask import jsonify, request
from flask_login import current_user, login_required

from app import db
from app.models import ExternalSyncRecord, WasteBatch
from config import Config


def _api_key_ok() -> bool:
    return request.headers.get('X-API-Key') == Config.EXTERNAL_API_KEY


def _batch_dict(b: WasteBatch) -> dict:
    return {
        'id': b.id,
        'batch_code': b.batch_code,
        'trace_code': b.trace_code,
        'name': b.name,
        'category': b.category,
        'source_unit': b.source_unit,
        'quantity': b.quantity,
        'unit': b.unit,
        'storage_location': b.storage_location,
        'hazard_level': b.hazard_level,
        'responsible_person': b.responsible_person,
        'current_status': b.current_status,
        'is_abnormal': bool(b.is_abnormal),
        'created_at': b.created_at.isoformat() if b.created_at else None,
        'updated_at': b.updated_at.isoformat() if b.updated_at else None,
    }


def register_routes(app):
    @app.route('/api/v1/health')
    def api_health():
        return jsonify({'status': 'ok', 'api': 'v1'})

    @app.route('/api/v1/batches', methods=['GET'])
    def api_batches_list():
        if not _api_key_ok():
            return jsonify({'error': 'invalid or missing X-API-Key'}), 401
        rows = WasteBatch.query.order_by(WasteBatch.id.desc()).limit(500).all()
        return jsonify({'data': [_batch_dict(b) for b in rows]})

    @app.route('/api/v1/batches/<string:code>', methods=['GET'])
    def api_batch_detail(code):
        if not _api_key_ok():
            return jsonify({'error': 'invalid or missing X-API-Key'}), 401
        b = WasteBatch.query.filter(
            (WasteBatch.batch_code == code) | (WasteBatch.trace_code == code)
        ).first()
        if not b:
            return jsonify({'error': 'not found'}), 404
        return jsonify({'data': _batch_dict(b)})

    @app.route('/api/v1/integration/erp/person', methods=['POST'])
    def api_mock_erp_person():
        """Mock ERP callback: resolve responsible person by employee id."""
        if not _api_key_ok():
            return jsonify({'error': 'invalid or missing X-API-Key'}), 401
        body = request.get_json(force=True, silent=True) or {}
        rec = ExternalSyncRecord(
            source_system='ERP',
            direction='inbound',
            payload=json.dumps(body, ensure_ascii=False),
            status='received',
        )
        db.session.add(rec)
        db.session.commit()
        eid = body.get('employee_id', 'unknown')
        return jsonify(
            {
                'employee_id': eid,
                'name': f'Mock Operator {eid}',
                'department': 'Production — Unit A',
                'email': f'{eid}@plant.example',
            }
        )

    @app.route('/api/v1/integration/lims/result', methods=['POST'])
    def api_mock_lims():
        if not _api_key_ok():
            return jsonify({'error': 'invalid or missing X-API-Key'}), 401
        body = request.get_json(force=True, silent=True) or {}
        rec = ExternalSyncRecord(
            source_system='LIMS',
            direction='inbound',
            payload=json.dumps(body, ensure_ascii=False),
            status='received',
        )
        db.session.add(rec)
        db.session.commit()
        return jsonify(
            {
                'sample_id': body.get('sample_id'),
                'hazard_class': 'mock-class-II',
                'received_at': datetime.utcnow().isoformat() + 'Z',
            }
        )

    @app.route('/api/v1/me', methods=['GET'])
    @login_required
    def api_me():
        """Session-based API probe for integration tests (browser same-origin)."""
        if not current_user.is_authenticated:
            return jsonify({'authenticated': False}), 401
        return jsonify(
            {
                'authenticated': True,
                'username': current_user.username,
                'role': current_user.role,
            }
        )
