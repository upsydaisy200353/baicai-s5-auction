"""服务端拍卖引擎 — 公开同时叫价 + 倒计时落槌"""

from __future__ import annotations

import copy
import random
import time
from datetime import datetime
from typing import Any

from constants import POOL_LETTERS, POSITION_NAMES, POSITIONS

MIN_BID = 10
MIN_INCREMENT = 10
DEFAULT_BID_EXTENSION_SECONDS = 45
DEFAULT_NO_BID_TIMEOUT_SECONDS = 60


def _now_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _min_increment(_price: int) -> int:
    return MIN_INCREMENT


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
        self.remaining_pools: list[str] = []
        self.pending_pick: dict | None = None
        # 公开叫价
        self.current_price = 0
        self.current_leader: str | None = None
        self.live_bids: list[dict] = []
        self.captain_bids: dict[str, int | None] = {}
        self.bid_deadline_ms = 0
        self.no_bid_deadline_ms = 0
        self.bid_extension_seconds = DEFAULT_BID_EXTENSION_SECONDS
        self.no_bid_timeout_seconds = DEFAULT_NO_BID_TIMEOUT_SECONDS
        self._bid_seq = 0
        self.passed_captains: set[str] = set()
        self.used_buyout: set[str] = set()

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
        if cap["name"] in self.passed_captains:
            return False
        if position in self._captain_positions(cap):
            return False
        return True

    def captain_skip_reason(self, cap: dict, position: str) -> str | None:
        if cap["name"] in self.passed_captains:
            return "本轮已放弃"
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

    def _player_start_price(self) -> int:
        if not self.current_player:
            return MIN_BID
        return max(MIN_BID, int(self.current_player.get("startPrice") or MIN_BID))

    def _player_buyout_price(self) -> int | None:
        if not self.current_player:
            return None
        buyout = self.current_player.get("buyoutPrice")
        return int(buyout) if buyout else None

    def _min_next_bid(self) -> int:
        start = self._player_start_price()
        if self.current_price <= 0:
            return start
        return self.current_price + _min_increment(self.current_price)

    def set_timing(self, bid_extension_seconds: int, no_bid_timeout_seconds: int) -> None:
        self.bid_extension_seconds = max(5, min(300, bid_extension_seconds))
        self.no_bid_timeout_seconds = max(10, min(600, no_bid_timeout_seconds))

    def _has_active_bids(self) -> bool:
        return bool(self.current_leader) and self.current_price > 0

    def _reset_bid_timer(self) -> None:
        self.bid_deadline_ms = int(time.time() * 1000) + self.bid_extension_seconds * 1000
        self.no_bid_deadline_ms = 0

    def _start_no_bid_timer(self) -> None:
        self.no_bid_deadline_ms = int(time.time() * 1000) + self.no_bid_timeout_seconds * 1000
        self.bid_deadline_ms = 0

    def _active_deadline_ms(self) -> int:
        if self._has_active_bids():
            return self.bid_deadline_ms
        return self.no_bid_deadline_ms

    def _seconds_remaining(self) -> float:
        deadline = self._active_deadline_ms()
        if not deadline:
            return 0.0
        return max(0.0, (deadline - int(time.time() * 1000)) / 1000.0)

    def _reset_open_bid_state(self) -> None:
        self.current_price = 0
        self.current_leader = None
        self.live_bids = []
        self.captain_bids = {}
        self.passed_captains = set()
        self._bid_seq = 0
        self._start_no_bid_timer()

    def _record_bid(self, captain_name: str, amount: int) -> None:
        self._bid_seq += 1
        entry = {
            "id": self._bid_seq,
            "captain": captain_name,
            "amount": amount,
            "time": _now_time(),
        }
        self.live_bids.insert(0, entry)
        self.live_bids = self.live_bids[:40]
        self.captain_bids[captain_name] = amount
        self.current_price = amount
        self.current_leader = captain_name
        self._reset_bid_timer()

    def _build_open_bid_context(self) -> dict | None:
        if self.phase != "open_bid" or not self.current_player:
            return None
        position = self.current_player["position"]
        eligible = self.eligible_captains(position)
        leader = None
        if self.current_leader:
            leader = next(
                (c for c in self.captains if c["name"] == self.current_leader), None
            )
        buyout = self._player_buyout_price()
        captain_rows = []
        for cap in self.captains:
            can_bid = self.captain_can_bid(cap, position)
            buyout_used = cap["name"] in self.used_buyout
            can_buyout = (
                bool(buyout)
                and can_bid
                and not buyout_used
                and cap["funds"] >= (buyout or 0)
            )
            captain_rows.append(
                {
                    "name": cap["name"],
                    "funds": cap["funds"],
                    "latestBid": self.captain_bids.get(cap["name"]),
                    "isLeader": cap["name"] == self.current_leader,
                    "canBid": can_bid,
                    "canBuyout": can_buyout,
                    "buyoutUsed": buyout_used,
                    "skipReason": self.captain_skip_reason(cap, position),
                    "passed": cap["name"] in self.passed_captains,
                }
            )
        has_bids = self._has_active_bids()
        timeout_seconds = (
            self.bid_extension_seconds if has_bids else self.no_bid_timeout_seconds
        )
        return {
            "player": copy.deepcopy(self.current_player),
            "eligibleCaptains": [copy.deepcopy(c) for c in eligible],
            "currentPrice": self.current_price,
            "currentLeader": self.current_leader,
            "leaderCaptain": copy.deepcopy(leader) if leader else None,
            "minNextBid": self._min_next_bid(),
            "minIncrement": _min_increment(max(self.current_price, self._player_start_price())),
            "startPrice": self._player_start_price(),
            "buyoutPrice": buyout,
            "hasBids": has_bids,
            "deadlineMs": self._active_deadline_ms(),
            "noBidDeadlineMs": self.no_bid_deadline_ms,
            "bidDeadlineMs": self.bid_deadline_ms,
            "bidExtensionSeconds": self.bid_extension_seconds,
            "noBidTimeoutSeconds": self.no_bid_timeout_seconds,
            "timeoutSeconds": timeout_seconds,
            "secondsRemaining": round(self._seconds_remaining(), 1),
            "liveBids": copy.deepcopy(self.live_bids),
            "captainRows": captain_rows,
        }

    def _maybe_hammer(self) -> None:
        if self.phase != "open_bid" or not self.current_player:
            return
        if self._seconds_remaining() > 0:
            return
        if self._has_active_bids():
            cap = next(c for c in self.captains if c["name"] == self.current_leader)
            self.add_log(
                f"{self.bid_extension_seconds}s 内无人加价 — {self.current_leader} 以 {self.current_price}w 拍得",
                "phase",
            )
            self._complete_sale(cap, self.current_price)
            return
        self.add_log(
            f"{self.no_bid_timeout_seconds}s 内无人出价 — 流拍",
            "warn",
        )
        player = self.current_player
        self._show_winner_reveal(player, None, None)

    def to_state(self) -> dict[str, Any]:
        self._maybe_hammer()
        return {
            "phase": self.phase,
            "captains": copy.deepcopy(self.captains),
            "players": copy.deepcopy(self.players),
            "poolOrder": list(self.pool_order),
            "currentPoolIndex": self.current_pool_index,
            "currentPool": self.current_pool,
            "currentPlayer": copy.deepcopy(self.current_player),
            "openBid": self._build_open_bid_context(),
            "logs": list(self.logs),
            "drawCandidates": copy.deepcopy(self.draw_candidates),
            "lastResult": copy.deepcopy(self.last_result),
            "availablePools": self.available_pools,
            "auctionSettings": {
                "bidExtensionSeconds": self.bid_extension_seconds,
                "noBidTimeoutSeconds": self.no_bid_timeout_seconds,
            },
        }

    def start(self) -> None:
        players, captains = self.players, self.captains
        captain_names = self.captain_names
        self.reset()
        self.players = players
        self.captains = captains
        self.captain_names = captain_names
        self.phase = "intro"
        self.add_log("公开叫价选人仪式开始", "phase")
        self.add_log("全员可同时加价，倒计时内无人继续加价则由最高价者拍得", "info")
        self.add_log(
            f"每次加价至少 {MIN_INCREMENT}w；加价后 {self.bid_extension_seconds}s 内无人继续加价则落槌",
            "info",
        )
        self.add_log(
            f"若 {self.no_bid_timeout_seconds}s 内尚无人出价则流拍；每位队长整场仅可一口价一次",
            "info",
        )
        self.add_log("每队每个位置仅可签下一名选手（含队长本人位置）", "info")

    def begin_pool_select(self) -> None:
        if self.phase != "intro":
            return
        self.phase = "pool_select"
        self.pool_order = []
        self.remaining_pools = list(POSITIONS)
        self.current_pool = None
        self.current_pool_index = -1
        self.add_log("请选择要拍卖的位置池（每池结束后可再选下一个）", "phase")

    def select_next_pool(self, pool: str) -> str | None:
        if self.phase != "pool_select":
            return "当前不在选择位置池阶段"
        if pool not in POSITIONS:
            return "无效位置池"
        if pool not in self.remaining_pools:
            return "该位置池已拍卖或不可选"

        self.remaining_pools.remove(pool)
        self.current_pool = pool
        self.pool_order.append(pool)
        self.current_pool_index = len(self.pool_order) - 1
        n = len(self.pool_order)
        self.add_log(
            f"管理员选择【{POSITION_NAMES[pool]}】池（第 {n}/5 个）",
            "phase",
        )

        has_players = bool(self.available_players(pool))
        has_bidders = bool(self.eligible_captains(pool))
        if has_players and has_bidders:
            self.add_log(f"【{POSITION_NAMES[pool]}】池 — 抽取拍卖标的", "phase")
            self._start_draw()
            return None

        if not has_players:
            self.add_log(f"【{POSITION_NAMES[pool]}】池已无选手，跳过", "warn")
        else:
            self.add_log(
                f"【{POSITION_NAMES[pool]}】池无人可竞拍（各队已有该位置选手），跳过",
                "warn",
            )
        self._end_current_pool()
        return None

    def _end_current_pool(self) -> None:
        finished = self.current_pool
        self.current_pool = None
        if not self.remaining_pools:
            self.phase = "finished"
            self.add_log("选人仪式圆满结束", "phase")
            return
        self.phase = "pool_select"
        remaining = "、".join(POSITION_NAMES[p] for p in self.remaining_pools)
        if finished:
            self.add_log(
                f"【{POSITION_NAMES[finished]}】池拍卖结束，请选择下一个位置池（剩余：{remaining}）",
                "phase",
            )
        else:
            self.add_log(f"请选择下一个位置池（剩余：{remaining}）", "phase")

    def _start_draw(self) -> None:
        if not self.current_pool:
            return
        pool = self.available_players(self.current_pool)
        if not pool:
            self._end_current_pool()
            return
        if not self.eligible_captains(self.current_pool):
            self.add_log(
                f"【{POSITION_NAMES[self.current_pool]}】池无人可竞拍（各队已有该位置选手）",
                "warn",
            )
            self._end_current_pool()
            return
        self.pending_pick = random.choice(pool)
        self.draw_candidates = copy.deepcopy(pool)
        self.current_player = None
        self.phase = "pool_draw"
        self.add_log(
            f"标的抽取 — {POSITION_NAMES[self.current_pool]} 池 · {len(pool)} 名候选",
            "info",
        )

    def reveal_draw(self) -> None:
        if self.phase != "pool_draw" or not self.pending_pick:
            return
        self.current_player = self.pending_pick
        self.pending_pick = None
        self.phase = "open_bid"
        self._reset_open_bid_state()
        pos = POSITION_NAMES[self.current_player["position"]]
        start = self._player_start_price()
        buyout = self._player_buyout_price()
        self.add_log(
            f"公开竞拍 — {self.current_player['serial']} {self.current_player['name']} · {pos}",
            "phase",
        )
        self.add_log(f"起拍 {start}w" + (f" · 一口价 {buyout}w" if buyout else ""), "info")

    def submit_open_bid(
        self,
        captain_name: str,
        action: str,
        amount: int | None = None,
    ) -> str | None:
        if self.phase != "open_bid" or not self.current_player:
            return "当前不在公开叫价阶段"

        cap = next((c for c in self.captains if c["name"] == captain_name), None)
        if not cap:
            return "队长不存在"

        position = self.current_player["position"]
        if action == "pass":
            if not self.captain_can_bid(cap, position) and captain_name not in self.passed_captains:
                reason = self.captain_skip_reason(cap, position)
                return f"不能参与本场竞拍（{reason}）"
            self.passed_captains.add(captain_name)
            self.captain_bids.setdefault(captain_name, None)
            self.add_log(f"[{captain_name}] 放弃本轮竞拍", "info")
            return None

        if action not in ("bid", "buyout"):
            return "无效操作"

        if not self.captain_can_bid(cap, position):
            reason = self.captain_skip_reason(cap, position)
            return f"不能参与本场竞拍（{reason}）"

        if amount is None:
            return "请指定出价金额"

        min_next = self._min_next_bid()
        buyout = self._player_buyout_price()

        if action == "buyout":
            if not buyout:
                return "该选手无一口价"
            if captain_name in self.used_buyout:
                return "本场仪式已使用过一口价机会（每位队长仅一次）"
            if amount < buyout:
                return f"一口价须为 {buyout}w"
            if amount > cap["funds"]:
                return "出价超出剩余资金"
            self.used_buyout.add(captain_name)
            self._record_bid(captain_name, buyout)
            self.add_log(f"[{captain_name}] 一口价 {buyout}w！", "buyout")
            cap = next(c for c in self.captains if c["name"] == captain_name)
            self._complete_sale(cap, buyout)
            return None

        if amount < min_next:
            return f"出价须 ≥ {min_next}w"
        if amount > cap["funds"]:
            return "出价超出剩余资金"

        self._record_bid(captain_name, amount)
        self.add_log(f"[{captain_name}] 出价 {amount}w", "bid")
        return None

    def hammer(self) -> str | None:
        if self.phase != "open_bid" or not self.current_player:
            return "当前不能落槌"
        if not self.current_leader or self.current_price <= 0:
            return "尚无人出价，无法落槌"
        cap = next(c for c in self.captains if c["name"] == self.current_leader)
        self.add_log(
            f"管理员落槌 — {self.current_leader} · {self.current_price}w",
            "phase",
        )
        self._complete_sale(cap, self.current_price)
        return None

    def _complete_sale(self, cap: dict, price: int) -> None:
        player = next(p for p in self.players if p["serial"] == self.current_player["serial"])
        player["sold"] = True
        player["finalPrice"] = price
        player["winner"] = cap["name"]
        cap["funds"] -= price
        cap["team"].append(player["name"])
        self._show_winner_reveal(player, cap["name"], price)

    def _show_winner_reveal(self, player: dict, winner: str | None, price: int | None) -> None:
        self.last_result = {
            "player": copy.deepcopy(player),
            "winner": winner,
            "price": price,
        }
        self.current_player = None
        self.phase = "winner_reveal"
        if winner and price is not None:
            self.add_log(f"成交：{winner} 以 {price}w 签下 {player['name']}", "win")
        else:
            self.add_log(f"流拍：{player['name']}", "warn")

    def confirm_winner(self) -> None:
        if self.phase != "winner_reveal":
            return
        self.last_result = None
        self.phase = "player_done"
        self._start_draw()


auction = AuctionEngine()
