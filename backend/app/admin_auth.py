from __future__ import annotations

import hmac
import os
import time
from collections import deque
from threading import Lock

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials


security = HTTPBasic()
_THROTTLE_LOCK = Lock()
_FAILURES_BY_IP_USER: dict[tuple[str, str], deque[float]] = {}
_FAILURES_BY_IP: dict[str, deque[float]] = {}
_LOCKED_UNTIL_BY_IP_USER: dict[tuple[str, str], float] = {}
_LOCKED_UNTIL_BY_IP: dict[str, float] = {}


def _env_int(name: str, default: int, *, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return max(minimum, parsed)


MAX_FAILED_ATTEMPTS = _env_int("FERRIC_ADMIN_MAX_FAILED_ATTEMPTS", 5)
MAX_FAILED_IP_ATTEMPTS = _env_int("FERRIC_ADMIN_MAX_FAILED_IP_ATTEMPTS", 30)
FAIL_WINDOW_SEC = _env_int("FERRIC_ADMIN_FAIL_WINDOW_SEC", 600)
LOCKOUT_SEC = _env_int("FERRIC_ADMIN_LOCKOUT_SEC", 900)


def _get_admin_credentials() -> tuple[str, str]:
    user = os.getenv("FERRIC_ADMIN_USER", "").strip()
    password = os.getenv("FERRIC_ADMIN_PASSWORD", "")
    if not user or not password:
        raise RuntimeError(
            "Admin credentials must be configured: set FERRIC_ADMIN_USER and FERRIC_ADMIN_PASSWORD."
        )
    return user, password


def validate_admin_credentials_config() -> None:
    _get_admin_credentials()


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _prune(now: float, bucket: deque[float]) -> None:
    threshold = now - FAIL_WINDOW_SEC
    while bucket and bucket[0] < threshold:
        bucket.popleft()


def _remaining_lock_seconds(now: float, ip: str, username: str) -> int:
    seconds = 0
    until_pair = _LOCKED_UNTIL_BY_IP_USER.get((ip, username))
    if until_pair and until_pair > now:
        seconds = max(seconds, int(until_pair - now) + 1)
    until_ip = _LOCKED_UNTIL_BY_IP.get(ip)
    if until_ip and until_ip > now:
        seconds = max(seconds, int(until_ip - now) + 1)
    return seconds


def _record_failure(now: float, ip: str, username: str) -> None:
    pair = (ip, username)
    pair_bucket = _FAILURES_BY_IP_USER.setdefault(pair, deque())
    pair_bucket.append(now)
    _prune(now, pair_bucket)
    if len(pair_bucket) >= MAX_FAILED_ATTEMPTS:
        _LOCKED_UNTIL_BY_IP_USER[pair] = now + LOCKOUT_SEC
        pair_bucket.clear()

    ip_bucket = _FAILURES_BY_IP.setdefault(ip, deque())
    ip_bucket.append(now)
    _prune(now, ip_bucket)
    if len(ip_bucket) >= MAX_FAILED_IP_ATTEMPTS:
        _LOCKED_UNTIL_BY_IP[ip] = now + LOCKOUT_SEC
        ip_bucket.clear()


def _clear_failures(ip: str, username: str) -> None:
    _FAILURES_BY_IP_USER.pop((ip, username), None)
    _FAILURES_BY_IP.pop(ip, None)
    _LOCKED_UNTIL_BY_IP_USER.pop((ip, username), None)
    _LOCKED_UNTIL_BY_IP.pop(ip, None)


def reset_admin_auth_throttle_state() -> None:
    with _THROTTLE_LOCK:
        _FAILURES_BY_IP_USER.clear()
        _FAILURES_BY_IP.clear()
        _LOCKED_UNTIL_BY_IP_USER.clear()
        _LOCKED_UNTIL_BY_IP.clear()


def require_admin(request: Request, credentials: HTTPBasicCredentials = Depends(security)) -> str:
    expected_user, expected_password = _get_admin_credentials()
    ip = _client_ip(request)
    username = credentials.username
    now = time.time()

    with _THROTTLE_LOCK:
        retry_after = _remaining_lock_seconds(now, ip, username)
    if retry_after > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user_ok = hmac.compare_digest(credentials.username, expected_user)
    pass_ok = hmac.compare_digest(credentials.password, expected_password)
    if not (user_ok and pass_ok):
        with _THROTTLE_LOCK:
            _record_failure(now, ip, username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    with _THROTTLE_LOCK:
        _clear_failures(ip, username)
    return credentials.username
