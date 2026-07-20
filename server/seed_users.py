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
_OLD_CAPTAIN_DEFAULTS = ("baicai-s5",)

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
    return os.environ.get("AUCTION_DEFAULT_CAPTAIN_PASSWORD", "baicai")


def _plain_for_role(role: str) -> str:
    return default_admin_password() if role == "admin" else default_captain_password()


def _password_hash_for_role(role: str) -> str:
    return hash_password(_plain_for_role(role))


def is_placeholder_password(stored: str) -> bool:
    return verify_password(_PLACEHOLDER_PLAIN, stored)


def _slug_username(name: str) -> str:
    mapped = CAPTAIN_NAME_TO_USERNAME.get(name)
    if mapped:
        return mapped
    slug = re.sub(r"[^a-z0-9]+", "", name.lower())
    return slug or f"captain_{abs(hash(name)) % 10000}"


def _set_password(user_id: int, plain: str) -> None:
    update_user_password(user_id, hash_password(plain), password_plain=plain)


def ensure_captain_user(captain_name: str) -> dict | None:
    """名单新增队长时同步创建登录账号。"""
    existing = get_user_by_captain_name(captain_name)
    if existing:
        return existing
    username = _slug_username(captain_name)
    plain = default_captain_password()
    return create_user(
        {
            "username": username,
            "passwordHash": hash_password(plain),
            "passwordPlain": plain,
            "role": "captain",
            "captainName": captain_name,
            "displayName": captain_name,
        }
    )


def seed_users() -> None:
    init_db()
    if count_users() > 0:
        return
    admin_plain = default_admin_password()
    create_user(
        {
            "username": ADMIN_USER["username"],
            "passwordHash": hash_password(admin_plain),
            "passwordPlain": admin_plain,
            "role": "admin",
            "captainName": None,
            "displayName": ADMIN_USER["displayName"],
        }
    )
    roster_captains = {
        e["name"] for e in list_roster() if e["identity"] == "captain"
    }
    cap_plain = default_captain_password()
    for username, captain_name in CAPTAIN_ACCOUNTS:
        if captain_name not in roster_captains:
            continue
        create_user(
            {
                "username": username,
                "passwordHash": hash_password(cap_plain),
                "passwordPlain": cap_plain,
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


def _guess_plain(user: dict) -> str | None:
    stored = user.get("passwordPlain")
    if stored:
        return stored
    candidates = [
        default_admin_password() if user["role"] == "admin" else default_captain_password(),
        "baicai-s5",
        "baicai-admin",
        "UDNB",
        "baicai",
        _PLACEHOLDER_PLAIN,
    ]
    seen: set[str] = set()
    for cand in candidates:
        if cand in seen:
            continue
        seen.add(cand)
        if verify_password(cand, user["passwordHash"]):
            return None if cand == _PLACEHOLDER_PLAIN else cand
    return None


def ensure_user_passwords() -> None:
    """升级免密占位；同步管理员/队长默认密码；回填明文供管理页展示。"""
    init_db()
    admin_plain = default_admin_password()
    cap_plain = default_captain_password()
    upgraded = 0

    for user in list_users():
        role = user["role"]
        desired = admin_plain if role == "admin" else cap_plain

        if is_placeholder_password(user["passwordHash"]):
            _set_password(user["id"], desired)
            upgraded += 1
            continue

        # 管理员：强制同步到配置默认
        if role == "admin" and not verify_password(desired, user["passwordHash"]):
            _set_password(user["id"], desired)
            print("Admin password synced to configured default")
            continue

        # 队长：统一同步到当前默认 baicai（杯赛现场统一口令）
        if role == "captain" and not verify_password(desired, user["passwordHash"]):
            _set_password(user["id"], desired)
            upgraded += 1
            continue
        if role == "captain" and verify_password(desired, user["passwordHash"]):
            if user.get("passwordPlain") != desired:
                update_user_password(user["id"], user["passwordHash"], password_plain=desired)
            continue

        # 其它：尽量回填可识别的明文
        if not user.get("passwordPlain"):
            guessed = _guess_plain(user)
            if guessed:
                update_user_password(user["id"], user["passwordHash"], password_plain=guessed)

    if upgraded:
        print(f"Upgraded {upgraded} account password(s) to current defaults")


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


def list_manageable_users() -> list[dict]:
    """管理页账号：管理员 + 现任名单队长。"""
    users = list_users()
    by_captain = {
        u["captainName"]: u
        for u in users
        if u["role"] == "captain" and u.get("captainName")
    }
    result: list[dict] = []
    for u in users:
        if u["role"] == "admin":
            result.append(u)
    for entry in list_roster():
        if entry.get("identity") != "captain":
            continue
        user = by_captain.get(entry["name"]) or ensure_captain_user(entry["name"])
        if user:
            # 重新取一遍以带上最新明文
            refreshed = next((x for x in list_users() if x["id"] == user["id"]), user)
            result.append(refreshed)
    return result


if __name__ == "__main__":
    reseed_users()
    print("Users seeded")
    print(f"  admin password: {default_admin_password()}")
    print(f"  captain default: {default_captain_password()}")
