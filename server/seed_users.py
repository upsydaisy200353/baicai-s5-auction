"""初始化用户账号"""

from auth import hash_password
from db import clear_users, count_users, create_user, init_db, list_roster

ADMIN_USER = {
    "username": "admin",
    "password": "admin123",
    "role": "admin",
    "displayName": "管理员",
}

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

DEFAULT_CAPTAIN_PASSWORD = "captain123"


def seed_users() -> None:
    init_db()
    if count_users() > 0:
        return
    create_user(
        {
            "username": ADMIN_USER["username"],
            "passwordHash": hash_password(ADMIN_USER["password"]),
            "role": "admin",
            "captainName": None,
            "displayName": ADMIN_USER["displayName"],
        }
    )
    roster_captains = {
        e["name"]
        for e in list_roster()
        if e["identity"] == "captain"
    }
    for username, captain_name in CAPTAIN_ACCOUNTS:
        if captain_name not in roster_captains:
            continue
        create_user(
            {
                "username": username,
                "passwordHash": hash_password(DEFAULT_CAPTAIN_PASSWORD),
                "role": "captain",
                "captainName": captain_name,
                "displayName": captain_name,
            }
        )


def reseed_users() -> None:
    init_db()
    clear_users()
    seed_users()


if __name__ == "__main__":
    reseed_users()
    print("Users seeded")
