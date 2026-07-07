"""初始化用户账号（房间口令登录）"""

from __future__ import annotations

import os
import re

from auth import hash_password
from db import clear_users, count_users, create_user, get_user_by_captain_name, init_db, list_roster, list_users, update_user_password

DEFAULT_ROOM_PASSWORD = "baicai-s5"

# username -> 队长名称（与名单 captain.name 一致）
CAPTAIN_ACCOUNTS = [
    ("wuyanzu", "吴彦祖"),
    ("yazi", "亚子"),
    ("caps", "caps"),
    ("baiweiyi", "白惟一"),
    ("mushroom", "🍄"),
    ("xxts", "xxts"),
    ("yume", "Yume"),
    ("pika", "皮卡"),
]

CAPTAIN_NAME_TO_USERNAME = {name: username for username, name in CAPTAIN_ACCOUNTS}

ADMIN_USER = {
    "username": "admin",
    "role": "admin",
    "displayName": "管理员",
}


def room_password() -> str:
    return os.environ.get("AUCTION_ROOM_PASSWORD", DEFAULT_ROOM_PASSWORD)


def room_password_hash() -> str:
    return hash_password(room_password())


def _slug_username(name: str) -> str:
    mapped = CAPTAIN_NAME_TO_USERNAME.get(name)
    if mapped:
        return mapped
    slug = re.sub(r"[^a-z0-9]+", "", name.lower())
    return slug or f"captain_{abs(hash(name)) % 10000}"


def ensure_captain_user(captain_name: str) -> dict | None:
    """名单新增队长时同步创建登录账号。"""
    existing = get_user_by_captain_name(captain_name)
    if existing:
        return existing
    username = _slug_username(captain_name)
    return create_user(
        {
            "username": username,
            "passwordHash": room_password_hash(),
            "role": "captain",
            "captainName": captain_name,
            "displayName": captain_name,
        }
    )


def sync_user_passwords() -> None:
    """将已有账号口令同步为当前房间口令（便于升级旧库）。"""
    pwd_hash = room_password_hash()
    for user in list_users():
        update_user_password(user["id"], pwd_hash)


def seed_users() -> None:
    init_db()
    if count_users() > 0:
        sync_user_passwords()
        return
    pwd_hash = room_password_hash()
    create_user(
        {
            "username": ADMIN_USER["username"],
            "passwordHash": pwd_hash,
            "role": "admin",
            "captainName": None,
            "displayName": ADMIN_USER["displayName"],
        }
    )
    roster_captains = {
        e["name"] for e in list_roster() if e["identity"] == "captain"
    }
    for username, captain_name in CAPTAIN_ACCOUNTS:
        if captain_name not in roster_captains:
            continue
        create_user(
            {
                "username": username,
                "passwordHash": pwd_hash,
                "role": "captain",
                "captainName": captain_name,
                "displayName": captain_name,
            }
        )
    for name in roster_captains:
        if name not in {n for _, n in CAPTAIN_ACCOUNTS}:
            ensure_captain_user(name)


def reseed_users() -> None:
    init_db()
    clear_users()
    seed_users()


def list_account_hints() -> dict:
    from db import list_users

    admin = None
    captains = []
    for user in list_users():
        if user["role"] == "admin":
            admin = {
                "username": user["username"],
                "displayName": user["displayName"],
                "role": "admin",
            }
        elif user["role"] == "captain":
            captains.append(
                {
                    "username": user["username"],
                    "displayName": user["displayName"],
                }
            )
    if not admin:
        admin = {"username": "admin", "displayName": "管理员", "role": "admin"}
    return {"admin": admin, "captains": captains, "captainCount": len(captains)}


if __name__ == "__main__":
    reseed_users()
    print("Users seeded")
