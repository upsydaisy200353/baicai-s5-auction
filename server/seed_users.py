"""初始化用户账号（免密登录，password_hash 仅占位）"""

from __future__ import annotations

import re

from auth import hash_password
from db import clear_users, count_users, create_user, get_user_by_captain_name, init_db, list_roster

_PLACEHOLDER_HASH = hash_password("__passwordless__")

ADMIN_USER = {
    "username": "admin",
    "role": "admin",
    "displayName": "管理员",
}

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
            "passwordHash": _PLACEHOLDER_HASH,
            "role": "captain",
            "captainName": captain_name,
            "displayName": captain_name,
        }
    )


def seed_users() -> None:
    init_db()
    if count_users() > 0:
        return
    create_user(
        {
            "username": ADMIN_USER["username"],
            "passwordHash": _PLACEHOLDER_HASH,
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
                "passwordHash": _PLACEHOLDER_HASH,
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
