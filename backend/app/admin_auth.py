from __future__ import annotations

import hmac
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials


security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    expected_user = os.getenv("FERRIC_ADMIN_USER", "admin")
    expected_password = os.getenv("FERRIC_ADMIN_PASSWORD", "admin")

    user_ok = hmac.compare_digest(credentials.username, expected_user)
    pass_ok = hmac.compare_digest(credentials.password, expected_password)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
