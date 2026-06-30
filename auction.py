"""拍卖核心逻辑"""

from __future__ import annotations

import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional

from data import CAPTAIN_NAMES, CAPTAINS, PLAYERS, POSITION_NAMES, Captain, Player


MIN_INCREMENT = 10
MAX_INCREMENT = 100


@dataclass
class BidAction:
    captain: str
    action: str  # "bid" | "pass" | "buyout"
    amount: int = 0
    increment: int = 0


@dataclass
class AuctionState:
    captains: list[Captain] = field(default_factory=list)
    players: list[Player] = field(default_factory=list)
    pool_order: list[str] = field(default_factory=list)
    current_pool: Optional[str] = None
    auction_log: list[str] = field(default_factory=list)
    verbose: bool = True

    def log(self, msg: str, *, force: bool = False) -> None:
        self.auction_log.append(msg)
        if self.verbose or force:
            print(msg)

    def available_players(self, position: str) -> list[Player]:
        return [
            p
            for p in self.players
            if p.position == position and not p.sold and p.name not in CAPTAIN_NAMES
        ]

    def active_captains(self) -> list[Captain]:
        return [c for c in self.captains if c.remaining > 0]

    def choose_pool_order(self) -> list[str]:
        """实力最弱队长优先决定位置池拍卖顺序"""
        order: list[str] = []
        remaining = list(POSITION_NAMES.keys())
        captains = sorted(self.captains, key=lambda c: c.rating)

        self.log("\n=== 位置池选择阶段 ===", force=True)
        self.log("规则：实力最弱队长优先选择，依次到最强", force=True)

        for cap in captains:
            if not remaining:
                break
            # demo 自动选择：优先选人数最多的池
            best = max(
                remaining,
                key=lambda pos: len(self.available_players(pos)),
            )
            order.append(best)
            remaining.remove(best)
            pos_cn = POSITION_NAMES[best]
            self.log(f"  [{cap.name}] (实力{cap.rating}) 选择 → {pos_cn}({best})", force=True)

        for pos in remaining:
            order.append(pos)

        self.pool_order = order
        return order

    def pick_random_player(self, position: str) -> Optional[Player]:
        pool = self.available_players(position)
        if not pool:
            return None
        player = random.choice(pool)
        self.log(f"\n>>> 从 {POSITION_NAMES[position]} 池随机抽出：{player.serial} {player.name}", force=True)
        self.log(f"    起拍价 {player.start_price}w | 一口价 {player.buyout_price}w", force=True)
        return player

    def bidding_order(self, round_num: int) -> list[Captain]:
        active = self.active_captains()
        if round_num == 1:
            return sorted(active, key=lambda c: c.rating, reverse=True)
        return sorted(active, key=lambda c: c.remaining)

    def run_player_auction(
        self,
        player: Player,
        bid_callback=None,
    ) -> Optional[Captain]:
        """
        对单个选手进行拍卖。
        bid_callback(captain, state, round_num, current_price, last_increment, is_first_round)
          -> BidAction | None  (None 表示 pass)
        """
        current_price = player.start_price
        highest: Optional[Captain] = None
        last_increment = MIN_INCREMENT
        round_num = 0

        self.log(f"\n--- 开始拍卖 {player.name} ---", force=True)

        while True:
            round_num += 1
            order = self.bidding_order(round_num)
            if self.verbose:
                if round_num == 1:
                    self.log("第1轮出价顺序（实力强→弱）：" + " → ".join(c.name for c in order))
                else:
                    self.log(f"第{round_num}轮出价顺序（资金少→多）：" + " → ".join(c.name for c in order))

            raised = False
            is_first = round_num == 1

            for cap in order:
                if highest and cap.name == highest.name:
                    continue
                if cap.remaining < current_price + MIN_INCREMENT:
                    self.log(f"  [{cap.name}] 资金不足，跳过 (剩余{cap.remaining}w)")
                    continue

                if bid_callback:
                    action = bid_callback(
                        cap, self, round_num, current_price, last_increment, is_first
                    )
                else:
                    action = auto_bid(
                        cap, current_price, last_increment, player.buyout_price, is_first
                    )

                if action is None or action.action == "pass":
                    self.log(f"  [{cap.name}] 放弃")
                    continue

                if action.action == "buyout":
                    if not is_first:
                        self.log(f"  [{cap.name}] 一口价仅首轮可用，视为放弃")
                        continue
                    if cap.remaining < player.buyout_price:
                        self.log(f"  [{cap.name}] 一口价资金不足")
                        continue
                    current_price = player.buyout_price
                    highest = cap
                    self.log(f"  [{cap.name}] ★ 一口价 {current_price}w 买断！", force=True)
                    player.final_price = current_price
                    player.winner = cap.name
                    player.sold = True
                    cap.funds -= current_price
                    cap.team.append(player.name)
                    return cap

                inc = max(MIN_INCREMENT, min(action.increment, MAX_INCREMENT))
                if round_num > 1 and inc < last_increment:
                    inc = last_increment
                new_price = current_price + inc
                if new_price > player.buyout_price:
                    new_price = player.buyout_price
                if new_price > cap.remaining:
                    self.log(f"  [{cap.name}] 出价超出剩余资金")
                    continue

                current_price = new_price
                last_increment = inc
                highest = cap
                raised = True
                self.log(
                    f"  [{cap.name}] 出价 {current_price}w (+{inc}w)",
                    force=not self.verbose,
                )
                if self.verbose:
                    self.log(f"      剩余{cap.remaining - current_price}w")

            if not raised:
                if highest:
                    self.log(f"\n>>> {highest.name} 以 {current_price}w 拍得 {player.name}（共{round_num}轮）", force=True)
                    player.final_price = current_price
                    player.winner = highest.name
                    player.sold = True
                    highest.funds -= current_price
                    highest.team.append(player.name)
                    return highest
                self.log(f"\n>>> 无人出价，{player.name} 流拍", force=True)
                return None

    def run_full_auction(self, bid_callback=None) -> None:
        self.choose_pool_order()

        for position in self.pool_order:
            self.current_pool = position
            pos_cn = POSITION_NAMES[position]
            self.log(f"\n{'=' * 50}", force=True)
            self.log(f"位置池：{pos_cn}({position})", force=True)
            self.log(f"{'=' * 50}", force=True)

            while True:
                player = self.pick_random_player(position)
                if not player:
                    self.log(f"{pos_cn} 池已空，进入下一位置", force=True)
                    break
                if not self.active_captains():
                    self.log("所有队长资金耗尽，拍卖结束", force=True)
                    return
                self.run_player_auction(player, bid_callback)

        self.print_summary()

    def print_summary(self) -> None:
        self.log("\n" + "=" * 50, force=True)
        self.log("拍卖结果汇总", force=True)
        self.log("=" * 50, force=True)
        for cap in self.captains:
            self.log(f"\n【{cap.name}】剩余 {cap.remaining}w", force=True)
            if cap.team:
                for name in cap.team:
                    p = next(x for x in self.players if x.name == name)
                    self.log(f"  - {p.serial} {name} @ {p.final_price}w", force=True)
            else:
                self.log("  （未拍得选手）", force=True)

        unsold = [p for p in self.players if not p.sold]
        if unsold:
            self.log("\n流拍选手：", force=True)
            for p in unsold:
                self.log(f"  {p.serial} {p.name}", force=True)


def auto_bid(
    cap: Captain,
    current_price: int,
    last_increment: int,
    buyout_price: int,
    is_first_round: bool,
) -> Optional[BidAction]:
    """简单 AI：根据资金与一口价比例决定是否跟价"""
    inc = max(last_increment, MIN_INCREMENT)
    target = min(current_price + inc, buyout_price)

    if target > cap.remaining:
        return None

    # 价格已接近一口价 80% 以上时，大概率放弃（模拟理性出价）
    price_ratio = current_price / buyout_price if buyout_price else 1
    if price_ratio >= 0.85 and random.random() < 0.7:
        return None

    # 首轮小概率直接一口价
    if is_first_round and cap.remaining >= buyout_price and random.random() < 0.05:
        return BidAction(cap.name, "buyout", buyout_price)

    if random.random() < 0.45:
        return BidAction(cap.name, "bid", target, inc)

    return None


def create_state(*, verbose: bool = False) -> AuctionState:
    return AuctionState(
        captains=deepcopy(CAPTAINS),
        players=deepcopy(PLAYERS),
        verbose=verbose,
    )
