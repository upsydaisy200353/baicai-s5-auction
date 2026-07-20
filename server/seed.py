"""初始化名单数据 — 白菜杯 S5 拍卖名单"""

from db import clear_roster, count_roster, create_entry, init_db

# 来源：白菜杯S5名单（拍卖用）.csv
# 有「队长资金」的为队长（昵称作登录名）；选手名为游戏 ID；rating 为 CSV 文本档位
SEED_ROWS: list[dict] = [
    {'identity': 'player', 'serial': 'A1', 'name': '不曾说破', 'poolLetter': 'A', 'startPrice': 850, 'buyoutPrice': 1750, 'rating': 'UR', 'weight': 1},
    {'identity': 'captain', 'name': '暂别langx', 'poolLetter': 'A', 'startPrice': 600, 'funds': 2700, 'rating': 'SSR'},
    {'identity': 'player', 'serial': 'A2', 'name': '伤痛之式#80197', 'poolLetter': 'A', 'startPrice': 600, 'buyoutPrice': 1250, 'rating': 'SSR', 'weight': 1},
    {'identity': 'player', 'serial': 'A3', 'name': '日会落#82969', 'poolLetter': 'A', 'startPrice': 350, 'buyoutPrice': 750, 'rating': 'SR+', 'weight': 1},
    {'identity': 'player', 'serial': 'A4', 'name': '素质青年#28017', 'poolLetter': 'A', 'startPrice': 350, 'buyoutPrice': 750, 'rating': 'SR', 'weight': 1},
    {'identity': 'player', 'serial': 'A5', 'name': '吴彦祖#95651', 'poolLetter': 'A', 'startPrice': 400, 'buyoutPrice': 850, 'rating': 'SR+', 'weight': 1},
    {'identity': 'player', 'serial': 'A6', 'name': '冷艳小妈#82914', 'poolLetter': 'A', 'startPrice': 200, 'buyoutPrice': 600, 'rating': 'SR', 'weight': 1},
    {'identity': 'player', 'serial': 'A7', 'name': '可以孤雨#56986', 'poolLetter': 'A', 'startPrice': 300, 'buyoutPrice': 650, 'rating': 'SR', 'weight': 1},
    {'identity': 'player', 'serial': 'A8', 'name': '向你的女王低头', 'poolLetter': 'A', 'startPrice': 200, 'buyoutPrice': 500, 'rating': 'SR-', 'weight': 1},
    {'identity': 'player', 'serial': 'A9', 'name': '你算哪块小饼干#85639', 'poolLetter': 'A', 'startPrice': 100, 'buyoutPrice': 300, 'rating': 'R', 'weight': 1},
    {'identity': 'player', 'serial': 'B1', 'name': '待定', 'poolLetter': 'B', 'startPrice': 1050, 'buyoutPrice': 1950, 'rating': 'UR+', 'weight': 1},
    {'identity': 'player', 'serial': 'B2', 'name': '倚窗听雨妙趣横生', 'poolLetter': 'B', 'startPrice': 900, 'buyoutPrice': 1800, 'rating': 'UR', 'weight': 1},
    {'identity': 'player', 'serial': 'B3', 'name': 'JOKER#16584', 'poolLetter': 'B', 'startPrice': 650, 'buyoutPrice': 1350, 'rating': 'SSR', 'weight': 1},
    {'identity': 'player', 'serial': 'B4', 'name': '斗鱼时雨空#60494', 'poolLetter': 'B', 'startPrice': 575, 'buyoutPrice': 1100, 'rating': 'SSR', 'weight': 1},
    {'identity': 'captain', 'name': '龙', 'poolLetter': 'B', 'startPrice': 575, 'funds': 2650, 'rating': 'SSR'},
    {'identity': 'player', 'serial': 'B5', 'name': '白惟一#23577', 'poolLetter': 'B', 'startPrice': 400, 'buyoutPrice': 800, 'rating': 'SR', 'weight': 1},
    {'identity': 'player', 'serial': 'B6', 'name': 'EDG荡厂胖驼妹', 'poolLetter': 'B', 'startPrice': 400, 'buyoutPrice': 800, 'rating': 'SR', 'weight': 1},
    {'identity': 'player', 'serial': 'B7', 'name': '可以不想上班y#82762', 'poolLetter': 'B', 'startPrice': 350, 'buyoutPrice': 700, 'rating': 'SR', 'weight': 1},
    {'identity': 'player', 'serial': 'B8', 'name': '可以恶魔', 'poolLetter': 'B', 'startPrice': 325, 'buyoutPrice': 650, 'rating': 'SR', 'weight': 1},
    {'identity': 'captain', 'name': '佛系', 'poolLetter': 'C', 'startPrice': 800, 'funds': 2350, 'rating': 'SSR+'},
    {'identity': 'captain', 'name': 'baozi', 'poolLetter': 'C', 'startPrice': 700, 'funds': 2500, 'rating': 'SSR'},
    {'identity': 'player', 'serial': 'C1', 'name': '往事如风#28023', 'poolLetter': 'C', 'startPrice': 600, 'buyoutPrice': 1200, 'rating': 'SSR', 'weight': 1},
    {'identity': 'player', 'serial': 'C2', 'name': '三冠の泥棒乗風儿#38237', 'poolLetter': 'C', 'startPrice': 600, 'buyoutPrice': 1200, 'rating': 'SSR', 'weight': 1},
    {'identity': 'captain', 'name': '杰宝大王', 'poolLetter': 'C', 'startPrice': 600, 'funds': 2650, 'rating': 'SSR'},
    {'identity': 'player', 'serial': 'C3', 'name': '爱吃蔬菜田小娟#78721', 'poolLetter': 'C', 'startPrice': 450, 'buyoutPrice': 900, 'rating': 'SR+', 'weight': 1},
    {'identity': 'player', 'serial': 'C4', 'name': '哪都可以丶#62099', 'poolLetter': 'C', 'startPrice': 450, 'buyoutPrice': 900, 'rating': 'SR+', 'weight': 1},
    {'identity': 'player', 'serial': 'C5', 'name': 'ColaStorm#37571', 'poolLetter': 'C', 'startPrice': 400, 'buyoutPrice': 800, 'rating': 'SR', 'weight': 1},
    {'identity': 'player', 'serial': 'C6', 'name': 'Denji#91132', 'poolLetter': 'C', 'startPrice': 150, 'buyoutPrice': 350, 'rating': 'R+', 'weight': 1},
    {'identity': 'player', 'serial': 'C7', 'name': '可以糕菇#78115', 'poolLetter': 'C', 'startPrice': 150, 'buyoutPrice': 350, 'rating': 'R+', 'weight': 1},
    {'identity': 'player', 'serial': 'D1', 'name': '李相赫35855', 'poolLetter': 'D', 'startPrice': 950, 'buyoutPrice': 1850, 'rating': 'UR', 'weight': 1},
    {'identity': 'player', 'serial': 'D2', 'name': '喜欢黄礼志#69879', 'poolLetter': 'D', 'startPrice': 650, 'buyoutPrice': 1200, 'rating': 'SSR', 'weight': 1},
    {'identity': 'captain', 'name': 'xxts', 'poolLetter': 'D', 'startPrice': 650, 'funds': 2700, 'rating': 'SSR'},
    {'identity': 'player', 'serial': 'D3', 'name': 'SeiunSky#71560', 'poolLetter': 'D', 'startPrice': 650, 'buyoutPrice': 1200, 'rating': 'SSR', 'weight': 1},
    {'identity': 'player', 'serial': 'D4', 'name': '吹梦到西洲#46470', 'poolLetter': 'D', 'startPrice': 600, 'buyoutPrice': 1200, 'rating': 'SSR', 'weight': 1},
    {'identity': 'player', 'serial': 'D5', 'name': '雨中漫步#18450', 'poolLetter': 'D', 'startPrice': 350, 'buyoutPrice': 750, 'rating': 'SR', 'weight': 1},
    {'identity': 'player', 'serial': 'D6', 'name': '也曾是洛', 'poolLetter': 'D', 'startPrice': 350, 'buyoutPrice': 750, 'rating': 'SR+', 'weight': 1},
    {'identity': 'player', 'serial': 'D7', 'name': 'KiriharaQAQ', 'poolLetter': 'D', 'startPrice': 275, 'buyoutPrice': 650, 'rating': 'SR-', 'weight': 1},
    {'identity': 'player', 'serial': 'D8', 'name': '请你吃苦瓜#', 'poolLetter': 'D', 'startPrice': 50, 'buyoutPrice': 150, 'rating': 'R', 'weight': 1},
    {'identity': 'player', 'serial': 'E1', 'name': '0704', 'poolLetter': 'E', 'startPrice': 850, 'buyoutPrice': 1850, 'rating': 'UR', 'weight': 1},
    {'identity': 'player', 'serial': 'E2', 'name': 'Die4u', 'poolLetter': 'E', 'startPrice': 675, 'buyoutPrice': 1250, 'rating': 'SSR+', 'weight': 1},
    {'identity': 'player', 'serial': 'E3', 'name': '可以贝北#28566', 'poolLetter': 'E', 'startPrice': 575, 'buyoutPrice': 1100, 'rating': 'SSR-', 'weight': 1},
    {'identity': 'captain', 'name': '辛德瑞拉', 'poolLetter': 'E', 'startPrice': 425, 'funds': 2900, 'rating': 'SR+'},
    {'identity': 'captain', 'name': '坤', 'poolLetter': 'E', 'startPrice': 400, 'funds': 3000, 'rating': 'SR+'},
    {'identity': 'player', 'serial': 'E4', 'name': 'Phainon#93942', 'poolLetter': 'E', 'startPrice': 300, 'buyoutPrice': 700, 'rating': 'SR+', 'weight': 1},
    {'identity': 'player', 'serial': 'E5', 'name': '盛衡雨#10124', 'poolLetter': 'E', 'startPrice': 175, 'buyoutPrice': 400, 'rating': 'R+', 'weight': 1},
    {'identity': 'player', 'serial': 'E6', 'name': '可以幸运#28759', 'poolLetter': 'E', 'startPrice': 50, 'buyoutPrice': 150, 'rating': 'R-', 'weight': 1},
]

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
