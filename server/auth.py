"""用户认证"""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from db import get_user_by_id, get_user_by_username

JWT_SECRET = os.environ.get("AUCTION_JWT_SECRET", "baicai-s5-dev-secret-change-me")
JWT_ALG = "HS256"
JWT_EXPIRE_HOURS = 72

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    ).hex()
    return secrets.compare_digest(check, digest)


def create_token(user: dict[str, Any]) -> str:
    payload = {
        "sub": str(user["id"]),
        "role": user["role"],
        "username": user["username"],
        "captainName": user.get("captainName"),
        "displayName": user.get("displayName") or user["username"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已失效") from exc


def _user_payload(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "captainName": user.get("captainName"),
        "displayName": user.get("displayName") or user["username"],
    }


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "请先登录")
    data = decode_token(creds.credentials)
    user = get_user_by_id(int(data["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")
    return _user_payload(user)


async def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any] | None:
    if not creds:
        return None
    try:
        return await get_current_user(creds)
    except HTTPException:
        return None


async def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
    return user


async def require_captain_or_admin(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if user["role"] not in ("admin", "captain"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要队长或管理员权限")
    return user
