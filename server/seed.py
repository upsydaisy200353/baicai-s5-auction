"""初始化名单数据 — 白菜杯 S6 拍卖名单"""

from pathlib import Path
import json

from db import clear_roster, count_roster, create_entry, init_db

SEED_ROWS: list[dict] = json.loads(
    Path(__file__).with_name("s6_roster.json").read_text(encoding="utf-8")
)

def _with_defaults(row: dict) -> dict:
    out = dict(row)
    out.setdefault("rating", "")
    if out.get("identity") == "player":
        out.setdefault("weight", 1)
    return out


def sync_roster_ratings_from_seed() -> int:
    """把已有名单的评级同步为 seed 中的文本档位（按序号/姓名匹配）。"""
    from db import list_roster, update_entry

    by_serial = {r["serial"]: r for r in SEED_ROWS if r.get("serial")}
    by_name = {r["name"]: r for r in SEED_ROWS}
    updated = 0
    for e in list_roster():
        src = None
        if e.get("serial") and e["serial"] in by_serial:
            src = by_serial[e["serial"]]
        elif e["name"] in by_name:
            src = by_name[e["name"]]
        if not src:
            continue
        new_rating = str(src.get("rating") or "")
        if str(e.get("rating") or "") == new_rating:
            continue
        update_entry(e["id"], {**e, "rating": new_rating})
        updated += 1
    return updated


def seed_if_empty() -> None:
    init_db()
    if count_roster() > 0:
        return
    for i, row in enumerate(SEED_ROWS, start=1):
        create_entry({**_with_defaults(row), "sortOrder": i})


def reseed() -> None:
    init_db()
    clear_roster()
    for i, row in enumerate(SEED_ROWS, start=1):
        entry = create_entry({**_with_defaults(row), "sortOrder": i})
        if entry and entry["identity"] == "captain":
            try:
                from seed_users import ensure_captain_user

                ensure_captain_user(entry["name"])
            except Exception as exc:
                print(f"队长账号同步跳过 {entry['name']}: {exc}")
    try:
        from assign_avatars import assign_player_avatars

        assign_player_avatars()
    except Exception as exc:
        print(f"头像分配跳过: {exc}")


if __name__ == "__main__":
    reseed()
    print(f"Seeded {len(SEED_ROWS)} roster entries")
