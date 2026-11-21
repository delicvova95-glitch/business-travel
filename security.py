"""CSRF-токены и простые ограничители частоты запросов."""
import secrets
import time
from collections import defaultdict
from functools import wraps

from flask import abort, request, session

# --- CSRF -------------------------------------------------------------------

def get_csrf_token():
    """Возвращает токен текущей сессии, создавая при первом обращении."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


def csrf_protect():
    """Проверка токена для POST-запросов (вызывать из before_request)."""
    if request.method == "POST":
        token = session.get("_csrf_token")
        sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
        if not token or not secrets.compare_digest(token, sent):
            abort(400, description="Недействительный CSRF-токен. Обновите страницу.")


# --- Rate limit (в памяти процесса) ------------------------------------------

class RateLimiter:
    def __init__(self, limit, window_seconds):
        self.limit = limit
        self.window = window_seconds
        self._hits = defaultdict(list)

    def allow(self, key):
        now = time.monotonic()
        hits = [t for t in self._hits[key] if now - t < self.window]
        self._hits[key] = hits
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True


# Не более 5 заявок с одного IP за 10 минут
request_form_limiter = RateLimiter(limit=5, window_seconds=600)
# Не более 10 попыток входа в админку с одного IP за 10 минут
admin_login_limiter = RateLimiter(limit=10, window_seconds=600)


def client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            from flask import redirect, url_for
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper
