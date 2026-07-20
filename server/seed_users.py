"""初始化用户账号（密码登录）"""

from __future__ import annotations

import os
import re

from auth import hash_password, verify_password
from db import (
    clear_users,
    count_users,
    create_user,
    get_user_by_captain_name,
    init_db,
    list_roster,
    list_users,
    update_user_password,
)

# 历史免密占位口令；启动时会被换成真实默认密码
_PLACEHOLDER_PLAIN = "__passwordless__"

ADMIN_USER = {
    "username": "admin",
    "role": "admin",
    "displayName": "管理员",
}

CAPTAIN_ACCOUNTS = [
    ("langx", "暂别langx"),
    ("long", "龙"),
    ("foxi", "佛系"),
    ("baozi", "baozi"),
    ("jiebao", "杰宝大王"),
    ("xxts", "xxts"),
    ("cinderella", "辛德瑞拉"),
    ("kun", "坤"),
]

CAPTAIN_NAME_TO_USERNAME = {name: username for username, name in CAPTAIN_ACCOUNTS}


def default_admin_password() -> str:
    return os.environ.get("AUCTION_ADMIN_PASSWORD", "UDNB")


def default_captain_password() -> str:
    return os.environ.get("AUCTION_DEFAULT_CAPTAIN_PASSWORD", "baicai-s5")


def _password_hash_for_role(role: str) -> str:
    plain = default_admin_password() if role == "admin" else default_captain_password()
    return hash_password(plain)


def is_placeholder_password(stored: str) -> bool:
    return verify_password(_PLACEHOLDER_PLAIN, stored)


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
            "passwordHash": _password_hash_for_role("captain"),
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
            "passwordHash": _password_hash_for_role("admin"),
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
                "passwordHash": _password_hash_for_role("captain"),
                "role": "captain",
                "captainName": captain_name,
                "displayName": captain_name,
            }
        )
    for name in roster_captains:
        if name not in {n for _, n in CAPTAIN_ACCOUNTS}:
            ensure_captain_user(name)


def sync_roster_captain_users() -> None:
    """确保名单里每位队长都有登录账号。"""
    init_db()
    for entry in list_roster():
        if entry.get("identity") == "captain":
            ensure_captain_user(entry["name"])


def ensure_user_passwords() -> None:
    """升级免密占位账号；并强制将管理员密码同步为当前默认（UDNB）。"""
    init_db()
    upgraded = 0
    for user in list_users():
        if not is_placeholder_password(user["passwordHash"]):
            continue
        update_user_password(user["id"], _password_hash_for_role(user["role"]))
        upgraded += 1
    if upgraded:
        print(f"Upgraded {upgraded} passwordless account(s) to default passwords")

    # 管理员密码以配置为准，避免线上仍停留在旧默认（曾误为 baicai-s5）
    admin = next((u for u in list_users() if u["role"] == "admin"), None)
    if admin:
        desired = default_admin_password()
        if not verify_password(desired, admin["passwordHash"]):
            update_user_password(admin["id"], hash_password(desired))
            print(f"Admin password synced to configured default")


def reseed_users() -> None:
    init_db()
    clear_users()
    seed_users()


def list_account_hints() -> dict:
    """登录页身份列表：管理员 + 名单库中的现任队长（不含已淘汰的旧账号）。"""
    users = list_users()
    admin = None
    users_by_captain: dict[str, dict] = {}
    for user in users:
        if user["role"] == "admin":
            admin = {
                "username": user["username"],
                "displayName": user["displayName"],
                "role": "admin",
            }
        elif user["role"] == "captain" and user.get("captainName"):
            users_by_captain[user["captainName"]] = user

    captains = []
    for entry in list_roster():
        if entry.get("identity") != "captain":
            continue
        name = entry["name"]
        user = users_by_captain.get(name)
        if not user:
            user = ensure_captain_user(name)
        if not user:
            continue
        captains.append(
            {
                "username": user["username"],
                "displayName": name,
            }
        )

    if not admin:
        admin = {"username": "admin", "displayName": "管理员", "role": "admin"}
    return {"admin": admin, "captains": captains, "captainCount": len(captains)}


if __name__ == "__main__":
    reseed_users()
    print("Users seeded")
    print(f"  admin password: {default_admin_password()}")
    print(f"  captain default: {default_captain_password()}")
