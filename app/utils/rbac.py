"""Role-based access decorators for views and JSON APIs."""
from functools import wraps

from flask import abort, jsonify, request
from flask_login import current_user

from config import Config


def roles_required(*roles):
    """403 if logged-in user role not in roles. Login required."""

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.status != 'active':
                abort(403)
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)

        return wrapped

    return decorator


def api_roles_required(*roles):
    """JSON 401/403 for API routes."""

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'unauthorized'}), 401
            if current_user.status != 'active':
                return jsonify({'error': 'forbidden'}), 403
            if current_user.role not in roles:
                return jsonify({'error': 'forbidden'}), 403
            return fn(*args, **kwargs)

        return wrapped

    return decorator


def auditor_read_only():
    """Block mutating HTTP methods for auditors."""

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if (
                current_user.is_authenticated
                and current_user.role == Config.ROLE_AUDITOR
                and request.method not in ('GET', 'HEAD', 'OPTIONS')
            ):
                abort(403)
            return fn(*args, **kwargs)

        return wrapped

    return decorator


def mutating_roles_exclude_auditor():
    """Use on routes that allow GET for auditor but not POST (apply with method check inside)."""
    pass
