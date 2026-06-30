"""拍卖名单数据 — 序号前缀 A~E 对应 上单/打野/中单/下路/辅助"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Player:
    serial: str
    name: str
    start_price: int  # 起拍价（单位：w）
    buyout_price: int  # 一口价（单位：w）
    position: str = ""
    sold: bool = False
    final_price: Optional[int] = None
    winner: Optional[str] = None


@dataclass
class Captain:
    name: str
    rating: int  # 实力分（表格起拍价），决定首轮出价顺序
    funds: int  # 竞拍资金（单位：w）
    pool_letter: str = ""  # 表格所处分区 A~E
    team: list[str] = field(default_factory=list)

    @property
    def remaining(self) -> int:
        return self.funds


# A=上单 B=打野 C=中单 D=下路 E=辅助
POOL_LETTERS = {
    "A": "Top",
    "B": "Jungle",
    "C": "Mid",
    "D": "Bot",
    "E": "Support",
}

POSITION_NAMES = {
    "Top": "上单",
    "Jungle": "打野",
    "Mid": "中单",
    "Bot": "下路",
    "Support": "辅助",
}

POSITIONS = list(POSITION_NAMES.keys())

CAPTAIN_NAMES = frozenset(
    {"吴彦祖", "亚子", "caps", "白惟一", "🍄", "xxts", "Yume", "皮卡"}
)


def _p(serial: str, name: str, start: int, buyout: int) -> Player:
    letter = serial[0]
    return Player(serial, name, start, buyout, POOL_LETTERS[letter])


# 可被拍卖的选手（不含队长）
PLAYERS: list[Player] = [
    _p("A1", "蒜头王八", 500, 1600),
    _p("A2", "松花奶饼茶", 450, 1000),
    _p("A3", "日会落#82969", 300, 800),
    _p("A4", "素质青年", 300, 800),
    _p("A5", "mhw", 250, 650),
    _p("A6", "dddd", 150, 350),
    _p("B1", "寒殇雨丶", 700, 1500),
    _p("B2", "可以难忘m0小姐", 650, 1400),
    _p("B3", "雪乃", 300, 800),
    _p("B4", "晨初", 200, 800),
    _p("B5", "请您务必带我躺", 150, 350),
    _p("B6", "可以恶魔", 50, 150),
    _p("C1", "baozi", 600, 1300),
    _p("C2", "Jinx", 550, 1200),
    _p("C3", "明月", 450, 1000),
    _p("C4", "雨中漫步", 300, 800),
    _p("C5", "孤雨", 300, 800),
    _p("C6", "辛德瑞拉", 250, 700),
    _p("C7", "Cola", 200, 500),
    _p("D1", "李相赫#35855", 650, 1400),
    _p("D2", "梧玖", 450, 1100),
    _p("D3", "也曾是洛", 400, 900),
    _p("D4", "少加爷", 350, 800),
    _p("D5", "TonyLau", 200, 700),
    _p("D6", "可以宋", 150, 400),
    _p("D7", "Kirihara", 100, 300),
    _p("E1", "坤true硬躺摆", 400, 1000),
    _p("E2", "Die4u", 400, 1000),
    _p("E3", "泡芙", 350, 900),
    _p("E4", "可以贝北", 250, 750),
    _p("E5", "天空要下小雨了", 200, 600),
    _p("E6", "黑山羊#90506", 200, 600),
]

# 队长参与竞价，自身不会被拍卖
CAPTAINS: list[Captain] = [
    Captain("吴彦祖", 350, 2900, "A"),
    Captain("亚子", 100, 3200, "A"),
    Captain("caps", 550, 2600, "B"),
    Captain("白惟一", 250, 2950, "B"),
    Captain("🍄", 200, 3000, "C"),
    Captain("xxts", 500, 2700, "D"),
    Captain("Yume", 700, 2250, "E"),
    Captain("皮卡", 100, 3100, "E"),
]
