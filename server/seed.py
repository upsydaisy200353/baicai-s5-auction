"""初始化名单数据"""

from db import clear_roster, connect, count_roster, create_entry, init_db

# 与前端默认名单一致（sort_order 决定展示与表格顺序）
SEED_ROWS: list[dict] = [
    {"identity": "player", "serial": "A1", "name": "蒜头王八", "poolLetter": "A", "startPrice": 500, "buyoutPrice": 1600},
    {"identity": "player", "serial": "A2", "name": "松花奶饼茶", "poolLetter": "A", "startPrice": 450, "buyoutPrice": 1000},
    {"identity": "captain", "name": "吴彦祖", "poolLetter": "A", "startPrice": 350, "funds": 2900},
    {"identity": "player", "serial": "A3", "name": "日会落#82969", "poolLetter": "A", "startPrice": 300, "buyoutPrice": 800},
    {"identity": "player", "serial": "A4", "name": "素质青年", "poolLetter": "A", "startPrice": 300, "buyoutPrice": 800},
    {"identity": "player", "serial": "A5", "name": "mhw", "poolLetter": "A", "startPrice": 250, "buyoutPrice": 650},
    {"identity": "player", "serial": "A6", "name": "dddd", "poolLetter": "A", "startPrice": 150, "buyoutPrice": 350},
    {"identity": "captain", "name": "亚子", "poolLetter": "A", "startPrice": 100, "funds": 3200},
    {"identity": "player", "serial": "B1", "name": "寒殇雨丶", "poolLetter": "B", "startPrice": 700, "buyoutPrice": 1500},
    {"identity": "player", "serial": "B2", "name": "可以难忘m0小姐", "poolLetter": "B", "startPrice": 650, "buyoutPrice": 1400},
    {"identity": "captain", "name": "caps", "poolLetter": "B", "startPrice": 550, "funds": 2600},
    {"identity": "player", "serial": "B3", "name": "雪乃", "poolLetter": "B", "startPrice": 300, "buyoutPrice": 800},
    {"identity": "captain", "name": "白惟一", "poolLetter": "B", "startPrice": 250, "funds": 2950},
    {"identity": "player", "serial": "B4", "name": "晨初", "poolLetter": "B", "startPrice": 200, "buyoutPrice": 800},
    {"identity": "player", "serial": "B5", "name": "请您务必带我躺", "poolLetter": "B", "startPrice": 150, "buyoutPrice": 350},
    {"identity": "player", "serial": "B6", "name": "可以恶魔", "poolLetter": "B", "startPrice": 50, "buyoutPrice": 150},
    {"identity": "player", "serial": "C1", "name": "baozi", "poolLetter": "C", "startPrice": 600, "buyoutPrice": 1300},
    {"identity": "player", "serial": "C2", "name": "Jinx", "poolLetter": "C", "startPrice": 550, "buyoutPrice": 1200},
    {"identity": "player", "serial": "C3", "name": "明月", "poolLetter": "C", "startPrice": 450, "buyoutPrice": 1000},
    {"identity": "player", "serial": "C4", "name": "雨中漫步", "poolLetter": "C", "startPrice": 300, "buyoutPrice": 800},
    {"identity": "player", "serial": "C5", "name": "孤雨", "poolLetter": "C", "startPrice": 300, "buyoutPrice": 800},
    {"identity": "player", "serial": "C6", "name": "辛德瑞拉", "poolLetter": "C", "startPrice": 250, "buyoutPrice": 700},
    {"identity": "captain", "name": "🍄", "poolLetter": "C", "startPrice": 200, "funds": 3000},
    {"identity": "player", "serial": "C7", "name": "Cola", "poolLetter": "C", "startPrice": 200, "buyoutPrice": 500},
    {"identity": "player", "serial": "D1", "name": "李相赫#35855", "poolLetter": "D", "startPrice": 650, "buyoutPrice": 1400},
    {"identity": "captain", "name": "xxts", "poolLetter": "D", "startPrice": 500, "funds": 2700},
    {"identity": "player", "serial": "D2", "name": "梧玖", "poolLetter": "D", "startPrice": 450, "buyoutPrice": 1100},
    {"identity": "player", "serial": "D3", "name": "也曾是洛", "poolLetter": "D", "startPrice": 400, "buyoutPrice": 900},
    {"identity": "player", "serial": "D4", "name": "少加爷", "poolLetter": "D", "startPrice": 350, "buyoutPrice": 800},
    {"identity": "player", "serial": "D5", "name": "TonyLau", "poolLetter": "D", "startPrice": 200, "buyoutPrice": 700},
    {"identity": "player", "serial": "D6", "name": "可以宋", "poolLetter": "D", "startPrice": 150, "buyoutPrice": 400},
    {"identity": "player", "serial": "D7", "name": "Kirihara", "poolLetter": "D", "startPrice": 100, "buyoutPrice": 300},
    {"identity": "captain", "name": "Yume", "poolLetter": "E", "startPrice": 700, "funds": 2250},
    {"identity": "player", "serial": "E1", "name": "坤true硬躺摆", "poolLetter": "E", "startPrice": 400, "buyoutPrice": 1000},
    {"identity": "player", "serial": "E2", "name": "Die4u", "poolLetter": "E", "startPrice": 400, "buyoutPrice": 1000},
    {"identity": "player", "serial": "E3", "name": "泡芙", "poolLetter": "E", "startPrice": 350, "buyoutPrice": 900},
    {"identity": "player", "serial": "E4", "name": "可以贝北", "poolLetter": "E", "startPrice": 250, "buyoutPrice": 750},
    {"identity": "player", "serial": "E5", "name": "天空要下小雨了", "poolLetter": "E", "startPrice": 200, "buyoutPrice": 600},
    {"identity": "player", "serial": "E6", "name": "黑山羊#90506", "poolLetter": "E", "startPrice": 200, "buyoutPrice": 600},
    {"identity": "captain", "name": "皮卡", "poolLetter": "E", "startPrice": 100, "funds": 3100},
]


def seed_if_empty() -> None:
    init_db()
    if count_roster() > 0:
        return
    for i, row in enumerate(SEED_ROWS, start=1):
        create_entry({**row, "sortOrder": i})


def reseed() -> None:
    init_db()
    clear_roster()
    for i, row in enumerate(SEED_ROWS, start=1):
        create_entry({**row, "sortOrder": i})


if __name__ == "__main__":
    reseed()
    print(f"Seeded {len(SEED_ROWS)} roster entries")
