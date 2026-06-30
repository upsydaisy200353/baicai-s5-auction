"""服务端拍卖引擎（多人同步）"""

from __future__ import annotations

import copy
import random
from datetime import datetime
from typing import Any

from constants import POOL_LETTERS, POSITION_NAMES, POSITIONS

MIN_INCREMENT = 10
MAX_INCREMENT = 100


def _now_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


class AuctionEngine:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.phase = "idle"
        self.captains: list[dict] = []
        self.players: list[dict] = []
        self.captain_names: set[str] = set()
        self.pool_order: list[str] = []
        self.current_pool_index = 0
        self.current_pool: str | None = None
        self.current_player: dict | None = None
        self.draw_candidates: list[dict] = []
        self.last_result: dict | None = None
        self.logs: list[dict] = []
        self._log_id = 0
        self.round_num = 0
        self.current_price = 0
        self.highest_bidder: dict | None = None
        self.last_increment = MIN_INCREMENT
        self.turn_index = 0
        self.order: list[dict] = []
        self.raised_this_round = False
        self.last_buyout = False
        self.bidding: dict | None = None
        self.remaining_pools: list[str] = []
        self.pending_pick: dict | None = None
        self.bid_order_names: list[str] = []
        self.passed_captains: set[str] = set()

    def load_roster(self, players: list[dict], captains: list[dict]) -> None:
        self.players = copy.deepcopy(players)
        self.captains = copy.deepcopy(
            [{**c, "team": list(c.get("team", []))} for c in captains]
        )
        self.captain_names = {c["name"] for c in captains}

    def add_log(self, text: str, log_type: str = "info") -> None:
        self._log_id += 1
        self.logs.append(
            {"id": self._log_id, "time": _now_time(), "text": text, "type": log_type}
        )

    def active_captains(self) -> list[dict]:
        return [c for c in self.captains if c["funds"] > 0]

    def _captain_own_position(self, cap: dict) -> str | None:
        letter = cap.get("poolLetter")
        if letter and letter in POOL_LETTERS:
            return POOL_LETTERS[letter]
        return cap.get("position")

    def _captain_positions(self, cap: dict) -> set[str]:
        positions: set[str] = set()
        own = self._captain_own_position(cap)
        if own:
            positions.add(own)
        for name in cap.get("team", []):
            player = next((p for p in self.players if p["name"] == name), None)
            if player:
                positions.add(player["position"])
        return positions

    def captain_can_bid(self, cap: dict, position: str) -> bool:
        if cap["funds"] <= 0:
            return False
        if position in self._captain_positions(cap):
            return False
        return True

    def captain_skip_reason(self, cap: dict, position: str) -> str | None:
        if cap["funds"] <= 0:
            return "资金不足"
        own = self._captain_own_position(cap)
        if own == position:
            return f"本人为{POSITION_NAMES[position]}"
        if position in self._captain_positions(cap):
            return f"已有{POSITION_NAMES[position]}选手"
        return None

    def eligible_captains(self, position: str) -> list[dict]:
        return [c for c in self.captains if self.captain_can_bid(c, position)]

    def _active_bidders(self, position: str) -> list[dict]:
        return [
            c
            for c in self.eligible_captains(position)
            if c["name"] not in self.passed_captains
        ]

    def _min_raise(self) -> int:
        if self.round_num <= 1:
            return MIN_INCREMENT
        return max(MIN_INCREMENT, self.last_increment)

    def _min_next_bid(self) -> int:
        if not self.current_player:
            return 0
        if self.highest_bidder is None:
            return self.current_player["startPrice"]
        raw = self.current_price + self._min_raise()
        return self._ceil_to_10(raw)

    @staticmethod
    def _ceil_to_10(value: int) -> int:
        return ((value + 9) // 10) * 10

    def _validate_bid_amount(self, cap: dict, amount: int) -> str | None:
        if not self.current_player:
            return "当前无拍卖选手"
        if amount % 10 != 0:
            return "出价须为 10 的倍数"
        buyout = self.current_player["buyoutPrice"]
        if amount > buyout:
            return f"出价不能超过一口价 {buyout}w"
        if amount > cap["funds"]:
            return "出价超出剩余资金"
        start = self.current_player["startPrice"]
        if self.highest_bidder is None:
            if amount < start:
                return f"出价不能低于起拍价 {start}w"
            return None
        if amount <= self.current_price:
            return f"必须高于当前价 {self.current_price}w"
        min_bid = self._min_next_bid()
        if amount < min_bid:
            return f"最低出价 {min_bid}w（加价不少于 {self._min_raise()}w）"
        return None

    def _maybe_hammer(self) -> bool:
        """落槌：其余竞拍者均已放弃时，最高价者胜出"""
        if not self.current_player or not self.highest_bidder:
            return False
        position = self.current_player["position"]
        others = [
            c
            for c in self._active_bidders(position)
            if c["name"] != self.highest_bidder["name"]
        ]
        if not others:
            self.add_log("其余竞拍者均已放弃，落槌成交", "phase")
            self._complete_sale(self.highest_bidder, self.current_price, False)
            return True
        return False

    def _default_bid_order_names(self) -> list[str]:
        return [c["name"] for c in sorted(self.captains, key=lambda c: c["rating"], reverse=True)]

    def _sort_bid_order(self, eligible: list[dict], round_num: int) -> list[dict]:
        if self.bid_order_names:
            rank = {name: i for i, name in enumerate(self.bid_order_names)}
            return sorted(eligible, key=lambda c: rank.get(c["name"], 999))
        if round_num == 1:
            return sorted(eligible, key=lambda c: c["rating"], reverse=True)
        return sorted(eligible, key=lambda c: c["funds"])

    def available_players(self, position: str) -> list[dict]:
        return [
            p
            for p in self.players
            if p["position"] == position
            and not p["sold"]
            and p["name"] not in self.captain_names
        ]

    @property
    def available_pools(self) -> list[str]:
        if self.phase != "pool_select":
            return []
        return list(self.remaining_pools)

    def to_state(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "captains": copy.deepcopy(self.captains),
            "players": copy.deepcopy(self.players),
            "poolOrder": list(self.pool_order),
            "currentPoolIndex": self.current_pool_index,
            "currentPool": self.current_pool,
            "currentPlayer": copy.deepcopy(self.current_player),
            "bidding": copy.deepcopy(self.bidding),
            "logs": list(self.logs),
            "drawCandidates": copy.deepcopy(self.draw_candidates),
            "lastResult": copy.deepcopy(self.last_result),
            "availablePools": self.available_pools,
            "bidOrder": list(self.bid_order_names),
        }

    def start(self) -> None:
        players, captains = self.players, self.captains
        captain_names = self.captain_names
        self.reset()
        self.players = players
        self.captains = captains
        self.captain_names = captain_names
        self.bid_order_names = []
        self.phase = "intro"
        self.add_log("白菜杯选人仪式开始", "phase")
        self.add_log("8 位队长将通过拍卖竞价组建战队", "info")
        self.add_log("规则：每队每个位置仅可签下一名选手（含队长本人位置）", "info")

    def begin_pool_select(self) -> None:
        if self.phase != "intro":
            return
        self.phase = "pool_select"
        self.pool_order = []
        self.remaining_pools = list(POSITIONS)
        self.add_log("第一阶段：管理员确定位置池拍卖顺序", "phase")

    def set_pool_order(self, order: list[str]) -> str | None:
        if self.phase != "pool_select":
            return "当前不在设定顺序阶段"
        if len(order) != len(POSITIONS):
            return "须包含全部 5 个位置池"
        if set(order) != set(POSITIONS):
            return "位置池不能重复或缺少"
        self.pool_order = list(order)
        self.remaining_pools = []
        labels = " → ".join(POSITION_NAMES[p] for p in order)
        self.add_log(f"位置池顺序：{labels}", "phase")
        self.current_pool_index = 0
        self._enter_bid_order_select()
        return None

    def set_bid_order(self, names: list[str]) -> str | None:
        if self.phase not in ("pool_select", "bid_order_select"):
            return "当前不能设定出价顺序"
        return self._apply_bid_order(names)

    def _apply_bid_order(self, names: list[str]) -> str | None:
        cap_names = {c["name"] for c in self.captains}
        if set(names) != cap_names:
            return "须包含全部队长且不能遗漏"
        if len(names) != len(set(names)):
            return "队长不能重复"
        self.bid_order_names = list(names)
        return None

    def confirm_bid_prep(self, names: list[str]) -> str | None:
        if self.phase != "bid_order_select":
            return "请先完成位置池顺序设定，并在出价顺序阶段确认"
        err = self._apply_bid_order(names)
        if err:
            return err
        pool = self.current_pool
        self.add_log(f"队长出价顺序：{' → '.join(names)}", "phase")
        if pool:
            self.add_log(f"【{POSITION_NAMES[pool]}】池开始抽签", "phase")
        self._start_draw()
        return None

    def _enter_bid_order_select(self) -> None:
        while self.current_pool_index < len(self.pool_order):
            pool = self.pool_order[self.current_pool_index]
            self.current_pool = pool
            has_players = bool(self.available_players(pool))
            has_bidders = bool(self.eligible_captains(pool))
            if has_players and has_bidders:
                if self.current_pool_index > 0:
                    self.bid_order_names = []
                self.phase = "bid_order_select"
                self.add_log(
                    f"请设定【{POSITION_NAMES[pool]}】池队长出价顺序"
                    f"（第 {self.current_pool_index + 1}/{len(self.pool_order)} 个位置池）",
                    "phase",
                )
                return
            if not has_players:
                self.add_log(f"【{POSITION_NAMES[pool]}】池已无选手，跳过", "warn")
            else:
                self.add_log(
                    f"【{POSITION_NAMES[pool]}】池无人可竞拍（各队已有该位置选手），跳过",
                    "warn",
                )
            self.current_pool_index += 1
        self.current_pool = None
        self.phase = "finished"
        self.add_log("选人仪式圆满结束", "phase")

    def _announce_pool(self) -> None:
        """兼容旧调用：进入出价顺序设定"""
        self._enter_bid_order_select()

    def confirm_pool_enter(self) -> None:
        if self.phase == "pool_announce":
            self._start_draw()

    def _start_draw(self) -> None:
        if not self.current_pool:
            return
        pool = self.available_players(self.current_pool)
        if not pool:
            self.current_pool_index += 1
            self._enter_bid_order_select()
            return
        if not self.eligible_captains(self.current_pool):
            self.add_log(
                f"【{POSITION_NAMES[self.current_pool]}】池无人可竞拍（各队已有该位置选手）",
                "warn",
            )
            self.current_pool_index += 1
            self._enter_bid_order_select()
            return
        self.pending_pick = random.choice(pool)
        self.draw_candidates = copy.deepcopy(pool)
        self.current_player = None
        self.phase = "pool_draw"
        self.add_log(f"随机抽取 — {POSITION_NAMES[self.current_pool]} 池", "info")

    def reveal_draw(self) -> None:
        if self.phase != "pool_draw" or not self.pending_pick:
            return
        self.current_player = self.pending_pick
        self.add_log(
            f"揭晓：{self.current_player['serial']} {self.current_player['name']}",
            "phase",
        )
        self.pending_pick = None
        self._begin_bidding()

    def _begin_bidding(self) -> None:
        if not self.current_player:
            return
        position = self.current_player["position"]
        if not self.eligible_captains(position):
            self.add_log(
                f"所有队长已拥有【{POSITION_NAMES[position]}】选手，{self.current_player['name']} 流拍",
                "warn",
            )
            self._show_winner_reveal(self.current_player, None, None)
            return
        self.phase = "bidding"
        self.round_num = 0
        self.current_price = self.current_player["startPrice"]
        self.highest_bidder = None
        self.last_increment = MIN_INCREMENT
        self.passed_captains = set()
        self.add_log(f"拍卖开始 — {self.current_player['name']}", "phase")
        self.add_log(
            f"起拍价 {self.current_player['startPrice']}w · 一口价 {self.current_player['buyoutPrice']}w · 加价须为 10 的倍数",
            "info",
        )
        self._start_new_round()

    def _start_new_round(self) -> None:
        if not self.current_player:
            return
        self.round_num += 1
        self.raised_this_round = False
        self.turn_index = 0
        position = self.current_player["position"]
        eligible = [
            c for c in self.eligible_captains(position) if c["name"] not in self.passed_captains
        ]
        self.order = self._sort_bid_order(eligible, self.round_num)
        if not self.order:
            self._finish_player_auction()
            return
        order_text = " → ".join(c["name"] for c in self.order)
        if self.bid_order_names:
            self.add_log(f"第 {self.round_num} 轮（管理员设定顺序）：{order_text}", "info")
        elif self.round_num == 1:
            self.add_log(f"第 1 轮（实力强→弱）：{order_text}", "info")
        else:
            self.add_log(f"第 {self.round_num} 轮（资金少→多）：{order_text}", "info")
        self._advance_turn()

    def _advance_turn(self) -> None:
        if not self.current_player or self.phase != "bidding":
            return
        while self.turn_index < len(self.order):
            cap = self.order[self.turn_index]
            self.turn_index += 1
            if cap["name"] in self.passed_captains:
                continue
            if self.highest_bidder and cap["name"] == self.highest_bidder["name"]:
                continue
            min_bid = self._min_next_bid()
            if cap["funds"] < min_bid:
                self.add_log(f"[{cap['name']}] 资金不足最低出价 {min_bid}w，跳过", "warn")
                continue
            self.bidding = {
                "player": copy.deepcopy(self.current_player),
                "currentPrice": self.current_price,
                "highestBidder": self.highest_bidder["name"] if self.highest_bidder else None,
                "roundNum": self.round_num,
                "lastIncrement": self.last_increment,
                "minNextBid": min_bid,
                "minRaise": self._min_raise(),
                "isFirstRound": self.round_num == 1,
                "turnCaptain": copy.deepcopy(cap),
                "order": copy.deepcopy(self.order),
                "passedCaptains": sorted(self.passed_captains),
            }
            return
        if not self.raised_this_round:
            self._finish_player_auction()
        else:
            self._start_new_round()

    def submit_bid(
        self,
        captain_name: str,
        action: str,
        amount: int | None = None,
        increment: int | None = None,
    ) -> str | None:
        if self.phase != "bidding" or not self.bidding or not self.current_player:
            return "当前不在竞价阶段"
        if self.bidding["turnCaptain"]["name"] != captain_name:
            return "还没轮到你出价"
        cap = next((c for c in self.captains if c["name"] == captain_name), None)
        if not cap:
            return "队长不存在"
        if captain_name in self.passed_captains:
            return "你已放弃本场竞拍"

        if action == "pass":
            self.passed_captains.add(cap["name"])
            self.add_log(f"[{cap['name']}] 放弃，退出本场竞拍", "info")
            self.bidding = None
            if self._maybe_hammer():
                return None
            self._advance_turn()
            return None

        position = self.current_player["position"]
        if not self.captain_can_bid(cap, position):
            reason = self.captain_skip_reason(cap, position)
            return f"不能参与本场竞拍（{reason}）"

        if action == "buyout":
            if self.round_num != 1:
                self.add_log(f"[{cap['name']}] 一口价仅首轮可用", "warn")
                self.bidding = None
                self._advance_turn()
                return None
            buyout = self.current_player["buyoutPrice"]
            if buyout % 10 != 0:
                return "一口价配置异常"
            if cap["funds"] < buyout:
                return "一口价资金不足"
            self._complete_sale(cap, buyout, True)
            return None

        if action != "bid":
            return "无效操作"

        bid_amount: int | None = amount
        if bid_amount is None and increment is not None:
            inc = max(MIN_INCREMENT, min(increment, MAX_INCREMENT))
            if self.highest_bidder is None:
                bid_amount = self.current_player["startPrice"]
                if inc > 0 and bid_amount == self.current_price:
                    bid_amount = self._ceil_to_10(self.current_price + inc)
            else:
                bid_amount = self._ceil_to_10(self.current_price + inc)
        if bid_amount is None:
            return "请指定出价金额"

        err = self._validate_bid_amount(cap, bid_amount)
        if err:
            return err

        prev_price = self.current_price
        if self.highest_bidder is None:
            self.current_price = bid_amount
            if bid_amount > self.current_player["startPrice"]:
                self.last_increment = bid_amount - self.current_player["startPrice"]
            else:
                self.last_increment = MIN_INCREMENT
        else:
            self.last_increment = bid_amount - prev_price
            self.current_price = bid_amount
        self.highest_bidder = cap
        self.raised_this_round = True
        if bid_amount > prev_price:
            self.add_log(
                f"[{cap['name']}] 出价 {bid_amount}w (+{bid_amount - prev_price}w)",
                "bid",
            )
        else:
            self.add_log(f"[{cap['name']}] 以起拍价 {bid_amount}w 应价", "bid")
        self.bidding = None
        self._advance_turn()
        return None

    def _complete_sale(self, cap: dict, price: int, buyout: bool) -> None:
        player = next(p for p in self.players if p["serial"] == self.current_player["serial"])
        player["sold"] = True
        player["finalPrice"] = price
        player["winner"] = cap["name"]
        cap["funds"] -= price
        cap["team"].append(player["name"])
        self.last_buyout = buyout
        if buyout:
            self.add_log(f"[{cap['name']}] ★ 一口价 {price}w 买断！", "buyout")
        self._show_winner_reveal(player, cap["name"], price)

    def _finish_player_auction(self) -> None:
        if self.highest_bidder:
            self._complete_sale(self.highest_bidder, self.current_price, False)
        elif self.current_player:
            self.add_log(f"{self.current_player['name']} 流拍", "warn")
            self._show_winner_reveal(self.current_player, None, None)

    def _show_winner_reveal(self, player: dict, winner: str | None, price: int | None) -> None:
        self.last_result = {
            "player": copy.deepcopy(player),
            "winner": winner,
            "price": price,
            "buyout": self.last_buyout,
        }
        self.bidding = None
        self.current_player = None
        self.phase = "winner_reveal"
        if winner and price is not None:
            self.add_log(f"成交：{winner} 以 {price}w 签下 {player['name']}", "win")

    def confirm_winner(self) -> None:
        if self.phase != "winner_reveal":
            return
        self.last_result = None
        self.phase = "player_done"
        self._start_draw()


# 全局单例
auction = AuctionEngine()
