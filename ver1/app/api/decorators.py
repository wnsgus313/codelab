from functools import wraps
from flask import g
from .errors import forbidden
from flask import abort
from flask_login import current_user
from ..models import Permission

def permission_required_vs(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('Insufficient permissions')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required_vs(f):
    return permission_required_vs(Permission.ADMIN)(f)

def prof_required_vs(f):
    return permission_required_vs(Permission.PROF)(f)

def moderator_required_vs(f):
    return permission_required_vs(Permission.AFFILIATE)(f)