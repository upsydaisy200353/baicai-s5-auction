"""为选手与队长分配头像：从 splash 目录随机复制到 frontend/public/player-avatars"""

from __future__ import annotations

import os
import random
import re
import shutil
from pathlib import Path

from db import init_db, list_roster, migrate_db, update_entry
from seed_users import CAPTAIN_ACCOUNTS

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
AVATAR_DIR = PROJECT_ROOT / "frontend" / "public" / "player-avatars"
DEFAULT_SPLASH_DIR = PROJECT_ROOT / "data" / "splash"
SPLASH_DIR = Path(os.environ.get("SPLASH_DIR", str(DEFAULT_SPLASH_DIR)))

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

CAPTAIN_NAME_TO_USERNAME = {name: username for username, name in CAPTAIN_ACCOUNTS}


def list_splash_images(splash_dir: Path) -> list[Path]:
    if not splash_dir.is_dir():
        return []
    return sorted(
        p for p in splash_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def avatar_public_path(key: str) -> str:
    return f"/player-avatars/{key}.jpg"


def avatar_file_path(key: str) -> Path:
    return AVATAR_DIR / f"{key}.jpg"


def captain_avatar_key(name: str, entry_id: int | None = None) -> str:
    slug = CAPTAIN_NAME_TO_USERNAME.get(name)
    if not slug:
        slug = re.sub(r"[^\w]", "", name.lower()) or f"id{entry_id or 0}"
    return f"captain-{slug}"


def _assign_entry_avatar(entry: dict, src: Path, key: str) -> None:
    dest = avatar_file_path(key)
    shutil.copy2(src, dest)
    avatar = avatar_public_path(key)
    update_entry(entry["id"], {"avatar": avatar})


def assign_player_avatars(
    splash_dir: Path | None = None,
    *,
    force: bool = False,
    seed: int | None = 42,
) -> int:
    """为选手与队长随机分配 splash 图。返回更新数量。"""
    migrate_db()
    splash_dir = splash_dir or SPLASH_DIR
    images = list_splash_images(splash_dir)
    if not images:
        print(f"未找到 splash 图片: {splash_dir}")
        return 0

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    if seed is not None:
        random.seed(seed)

    roster = list_roster()
    players = [e for e in roster if e["identity"] == "player" and e.get("serial")]
    captains = [e for e in roster if e["identity"] == "captain"]
    pool = images.copy()
    random.shuffle(pool)
    updated = 0
    idx = 0

    for player in players:
        serial = player["serial"]
        if not serial:
            continue
        if player.get("avatar") and not force and avatar_file_path(serial).is_file():
            idx += 1
            continue
        _assign_entry_avatar(player, pool[idx % len(pool)], serial)
        print(f"  [选手] {serial} {player['name']} <- {pool[idx % len(pool)].name}")
        idx += 1
        updated += 1

    for captain in captains:
        key = captain_avatar_key(captain["name"], captain["id"])
        if captain.get("avatar") and not force and avatar_file_path(key).is_file():
            idx += 1
            continue
        _assign_entry_avatar(captain, pool[idx % len(pool)], key)
        print(f"  [队长] {captain['name']} <- {pool[idx % len(pool)].name}")
        idx += 1
        updated += 1

    return updated


def ensure_avatar_db_paths() -> int:
    """若 public 目录已有头像文件，补全数据库路径。"""
    migrate_db()
    updated = 0
    for entry in list_roster():
        if entry["identity"] == "player":
            serial = entry.get("serial")
            if not serial or not avatar_file_path(serial).is_file():
                continue
            path = avatar_public_path(serial)
        else:
            key = captain_avatar_key(entry["name"], entry["id"])
            if not avatar_file_path(key).is_file():
                continue
            path = avatar_public_path(key)
        if entry.get("avatar") != path:
            update_entry(entry["id"], {"avatar": path})
            updated += 1
    return updated


if __name__ == "__main__":
    init_db()
    n = assign_player_avatars(force=True)
    print(f"已分配 {n} 个头像 -> {AVATAR_DIR}")
