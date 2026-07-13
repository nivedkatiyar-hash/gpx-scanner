from functools import wraps
from flask import session, abort

def require_subscription(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            abort(401)

        if session.get("subscription_status") != "active":
            abort(403)

        return view(*args, **kwargs)

    return wrapper
