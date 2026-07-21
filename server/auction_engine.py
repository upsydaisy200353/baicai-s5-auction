"""服务端拍卖引擎 — 全局加权抽签 + 公开同时叫价 + 流拍池二次拍卖"""

from __future__ import annotations

import copy
import json
import random
import time
from datetime import datetime
from typing import Any

from constants import POOL_LETTERS, POSITION_NAMES

MIN_BID = 10
MIN_INCREMENT = 20
DEFAULT_BID_EXTENSION_SECONDS = 30
DEFAULT_NO_BID_TIMEOUT_SECONDS = 60
UNSOLD_PRICE_MULTIPLIER = 1.25
SOFT_CAP_BASE = 7
HARD_CAP_BASE = 8
MIN_RESERVE_FUNDS = 200  # 队长必须保留的最低余额（单位：w）
MIN_TEAM_SIZE_FOR_RESERVE = 3  # 已有3名队员时启用保留限制

CAPTAIN_ALIAS_POOL = [
    "绯红印记树怪",
    "苍蓝雕纹魔像",
    "深红锋喙鸟",
    "锋喙鸟",
    "石甲虫",
    "暗影狼",
    "魔沼蛙",
    "峡谷迅捷蟹",
]


def _now_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _min_increment(_price: int) -> int:
    return MIN_INCREMENT


def _player_weight(player: dict) -> int:
    try:
        w = int(player.get("weight") or 1)
    except (TypeError, ValueError):
        w = 1
    return max(1, w)


class AuctionEngine:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.phase = "idle"
        self.captains: list[dict] = []
        self.players: list[dict] = []
        self.captain_names: set[str] = set()
        self._reset_ceremony_fields()

    def _reset_ceremony_fields(self) -> None:
        self.pool_order = []
        self.current_pool_index = 0
        self.current_pool = None
        self.current_player = None
        self.draw_candidates = []
        self.last_result = None
        self.logs = []
        self._log_id = 0
        self.remaining_pools = []
        self.pending_pick = None
        self.current_price = 0
        self.current_leader = None
        self.live_bids = []
        self.captain_bids = {}
        self.bid_deadline_ms = 0
        self.no_bid_deadline_ms = 0
        self.bid_extension_seconds = DEFAULT_BID_EXTENSION_SECONDS
        self.no_bid_timeout_seconds = DEFAULT_NO_BID_TIMEOUT_SECONDS
        self._bid_seq = 0
        self.passed_captains = set()
        self.used_buyout = set()
        self.captain_aliases: dict[str, str] = {}
        self.auction_stage = "main"  # main | unsold

    def reset_ceremony(self) -> None:
        """回到 idle，保留已加载名单与计时设置。"""
        players = copy.deepcopy(self.players)
        captains = copy.deepcopy(self.captains)
        captain_names = set(self.captain_names)
        bid_ext = self.bid_extension_seconds
        no_bid = self.no_bid_timeout_seconds
        self.reset()
        self.players = players
        self.captains = captains
        self.captain_names = captain_names
        self.bid_extension_seconds = bid_ext
        self.no_bid_timeout_seconds = no_bid
        self._normalize_players()
        self.phase = "idle"

    def is_in_progress(self) -> bool:
        return self.phase != "idle"

    def serialize(self) -> str:
        return json.dumps(
            {
                "phase": self.phase,
                "captains": self.captains,
                "players": self.players,
                "captainNames": list(self.captain_names),
                "poolOrder": self.pool_order,
                "currentPoolIndex": self.current_pool_index,
                "currentPool": self.current_pool,
                "currentPlayer": self.current_player,
                "drawCandidates": self.draw_candidates,
                "lastResult": self.last_result,
                "logs": self.logs,
                "_logId": self._log_id,
                "remainingPools": self.remaining_pools,
                "pendingPick": self.pending_pick,
                "currentPrice": self.current_price,
                "currentLeader": self.current_leader,
                "liveBids": self.live_bids,
                "captainBids": self.captain_bids,
                "bidDeadlineMs": self.bid_deadline_ms,
                "noBidDeadlineMs": self.no_bid_deadline_ms,
                "bidExtensionSeconds": self.bid_extension_seconds,
                "noBidTimeoutSeconds": self.no_bid_timeout_seconds,
                "_bidSeq": self._bid_seq,
                "passedCaptains": list(self.passed_captains),
                "usedBuyout": list(self.used_buyout),
                "captainAliases": self.captain_aliases,
                "auctionStage": self.auction_stage,
            },
            ensure_ascii=False,
        )

    def deserialize(self, raw: str) -> None:
        data = json.loads(raw)
        self.phase = data.get("phase", "idle")
        self.captains = data.get("captains", [])
        self.players = data.get("players", [])
        self.captain_names = set(data.get("captainNames", []))
        self.pool_order = data.get("poolOrder", [])
        self.current_pool_index = data.get("currentPoolIndex", 0)
        self.current_pool = data.get("currentPool")
        self.current_player = data.get("currentPlayer")
        self.draw_candidates = data.get("drawCandidates", [])
        self.last_result = data.get("lastResult")
        self.logs = data.get("logs", [])
        self._log_id = data.get("_logId", 0)
        self.remaining_pools = data.get("remainingPools", [])
        self.pending_pick = data.get("pendingPick")
        self.current_price = data.get("currentPrice", 0)
        self.current_leader = data.get("currentLeader")
        self.live_bids = data.get("liveBids", [])
        self.captain_bids = data.get("captainBids", {})
        self.bid_deadline_ms = data.get("bidDeadlineMs", 0)
        self.no_bid_deadline_ms = data.get("noBidDeadlineMs", 0)
        self.bid_extension_seconds = data.get(
            "bidExtensionSeconds", DEFAULT_BID_EXTENSION_SECONDS
        )
        self.no_bid_timeout_seconds = data.get(
            "noBidTimeoutSeconds", DEFAULT_NO_BID_TIMEOUT_SECONDS
        )
        self._bid_seq = data.get("_bidSeq", 0)
        self.passed_captains = set(data.get("passedCaptains", []))
        self.used_buyout = set(data.get("usedBuyout", []))
        self.captain_aliases = dict(data.get("captainAliases", {}))
        self.auction_stage = data.get("auctionStage", "main")
        # 兼容旧存档：pool_select → 直接进入抽签
        if self.phase == "pool_select":
            self.phase = "intro"
        self._normalize_players()

    def tick(self) -> bool:
        """后台计时：检查全员放弃与倒计时落槌。返回状态是否变化。"""
        if self.phase != "open_bid" or not self.current_player:
            return False
        before = (self.phase, self.current_leader, self.current_price, self.last_result)
        self._check_all_passed_early()
        self._maybe_hammer()
        after = (self.phase, self.current_leader, self.current_price, self.last_result)
        return before != after

    def load_roster(self, players: list[dict], captains: list[dict]) -> None:
        self.players = copy.deepcopy(players)
        self.captains = copy.deepcopy(
            [{**c, "team": list(c.get("team", []))} for c in captains]
        )
        self.captain_names = {c["name"] for c in captains}
        self._normalize_players()

    def _normalize_players(self) -> None:
        for p in self.players:
            start = max(MIN_BID, int(p.get("startPrice") or MIN_BID))
            if "originalStartPrice" not in p or p.get("originalStartPrice") is None:
                p["originalStartPrice"] = start
            p["startPrice"] = int(p.get("startPrice") or start)
            p["rating"] = str(p.get("rating") or "").strip()
            p["weight"] = _player_weight(p)
            p["sold"] = bool(p.get("sold", False))
            p["inUnsoldPool"] = bool(p.get("inUnsoldPool", False))
            p["excluded"] = bool(p.get("excluded", False))
            if p.get("finalPrice") is None:
                p["finalPrice"] = None
            if p.get("winner") is None:
                p["winner"] = None

    def add_log(self, text: str, log_type: str = "info") -> None:
        self._log_id += 1
        self.logs.append(
            {"id": self._log_id, "time": _now_time(), "text": text, "type": log_type}
        )

    def alias_for(self, captain_name: str | None) -> str | None:
        if not captain_name:
            return None
        return self.captain_aliases.get(captain_name, captain_name)

    def _label(self, captain_name: str) -> str:
        return self.captain_aliases.get(captain_name, captain_name)

    def _reshuffle_aliases(self) -> None:
        names = [c["name"] for c in self.captains]
        if not names:
            self.captain_aliases = {}
            return
        pool = list(CAPTAIN_ALIAS_POOL)
        random.shuffle(pool)
        if len(names) > len(pool):
            # 不够则追加编号后缀
            extra = [f"代号{i + 1}" for i in range(len(names) - len(pool))]
            pool.extend(extra)
        self.captain_aliases = {name: pool[i] for i, name in enumerate(names)}

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
        # 已有 MIN_TEAM_SIZE_FOR_RESERVE 名队员时，剩余资金必须 >= MIN_RESERVE_FUNDS
        if len(cap.get("team", [])) >= MIN_TEAM_SIZE_FOR_RESERVE:
            if cap["funds"] <= MIN_RESERVE_FUNDS:
                return False
        return True

    def captain_skip_reason(self, cap: dict, position: str) -> str | None:
        if cap["name"] in self.passed_captains:
            return "本轮已放弃"
        return self._position_skip_reason(cap, position)

    def _position_skip_reason(self, cap: dict, position: str) -> str | None:
        if cap["funds"] <= 0:
            return "资金不足"
        own = self._captain_own_position(cap)
        if own == position:
            return "位置限制"
        if position in self._captain_positions(cap):
            return "已有同位置选手"
        # 已有 MIN_TEAM_SIZE_FOR_RESERVE 名队员时，剩余资金必须 >= MIN_RESERVE_FUNDS
        if len(cap.get("team", [])) >= MIN_TEAM_SIZE_FOR_RESERVE:
            if cap["funds"] <= MIN_RESERVE_FUNDS:
                return f"需保留{MIN_RESERVE_FUNDS}w余额"
        return None

    def _could_bid_captains(self, position: str) -> list[dict]:
        return [c for c in self.captains if self._position_skip_reason(c, position) is None]

    def _check_all_passed_early(self) -> None:
        if self.phase != "open_bid" or not self.current_player or self._has_active_bids():
            return
        position = self.current_player["position"]
        could_bid = self._could_bid_captains(position)
        if not could_bid:
            return
        if all(cap["name"] in self.passed_captains for cap in could_bid):
            self.add_log("全员放弃 — 流拍", "warn")
            player = self.current_player
            self._show_winner_reveal(player, None, None)

    def eligible_captains(self, position: str) -> list[dict]:
        return [c for c in self.captains if self.captain_can_bid(c, position)]

    def _is_auctionable_player(self, p: dict) -> bool:
        return (
            not p.get("sold")
            and not p.get("excluded")
            and p.get("name") not in self.captain_names
        )

    def main_pool_players(self) -> list[dict]:
        return [
            p
            for p in self.players
            if self._is_auctionable_player(p) and not p.get("inUnsoldPool")
        ]

    def unsold_pool_players(self) -> list[dict]:
        return [
            p
            for p in self.players
            if self._is_auctionable_player(p) and p.get("inUnsoldPool")
        ]

    def drawable_players(self) -> list[dict]:
        """当前阶段可抽签选手：有至少一名可竞拍队长。"""
        pool = (
            self.unsold_pool_players()
            if self.auction_stage == "unsold"
            else self.main_pool_players()
        )
        return [p for p in pool if self._could_bid_captains(p["position"])]

    def available_players(self, position: str) -> list[dict]:
        """兼容旧接口：某位置未成交且未排除的选手。"""
        return [
            p
            for p in self.players
            if p["position"] == position and self._is_auctionable_player(p)
        ]

    @property
    def available_pools(self) -> list[str]:
        return []

    def _captain_count_for_position(self, position: str) -> int:
        return sum(
            1 for c in self.captains if self._captain_own_position(c) == position
        )

    def _sold_count_for_position(self, position: str) -> int:
        return sum(
            1
            for p in self.players
            if p["position"] == position
            and p.get("sold")
            and p.get("name") not in self.captain_names
        )

    def _apply_position_caps(self, position: str) -> None:
        n = self._captain_count_for_position(position)
        sold = self._sold_count_for_position(position)
        soft = SOFT_CAP_BASE - n
        hard = HARD_CAP_BASE - n
        moved_unsold = 0
        excluded = 0
        for p in self.players:
            if p["position"] != position:
                continue
            if p.get("sold") or p.get("name") in self.captain_names:
                continue
            if p.get("excluded"):
                continue
            if sold >= hard:
                p["excluded"] = True
                p["inUnsoldPool"] = False
                excluded += 1
            elif sold >= soft:
                if not p.get("inUnsoldPool"):
                    p["inUnsoldPool"] = True
                    moved_unsold += 1
        pos_name = POSITION_NAMES.get(position, position)
        if excluded:
            self.add_log(
                f"【{pos_name}】成交已达 {hard}（8−{n}），{excluded} 名选手不再出现",
                "warn",
            )
        elif moved_unsold:
            self.add_log(
                f"【{pos_name}】成交已达 {soft}（7−{n}），{moved_unsold} 名选手进入流拍池",
                "warn",
            )

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
                    "alias": self.captain_aliases.get(cap["name"]),
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
        random.shuffle(captain_rows)
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
            "captainAliases": dict(self.captain_aliases),
        }

    def _maybe_hammer(self) -> None:
        if self.phase != "open_bid" or not self.current_player:
            return
        if self._seconds_remaining() > 0:
            return
        if self._has_active_bids():
            cap = next(c for c in self.captains if c["name"] == self.current_leader)
            self.add_log(
                f"{self.bid_extension_seconds}s 内无人加价 — "
                f"{self._label(self.current_leader)} 以 {self.current_price}w 拍得",
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
            "pendingPick": copy.deepcopy(self.pending_pick),
            "openBid": self._build_open_bid_context(),
            "logs": list(self.logs),
            "drawCandidates": copy.deepcopy(self.draw_candidates),
            "lastResult": copy.deepcopy(self.last_result),
            "availablePools": self.available_pools,
            "auctionSettings": {
                "bidExtensionSeconds": self.bid_extension_seconds,
                "noBidTimeoutSeconds": self.no_bid_timeout_seconds,
            },
            "captainAliases": dict(self.captain_aliases),
            "auctionStage": self.auction_stage,
            "unsoldPoolCount": len(self.unsold_pool_players()),
            "mainPoolCount": len(self.main_pool_players()),
        }

    def start(self) -> None:
        players, captains = self.players, self.captains
        captain_names = self.captain_names
        self.reset()
        self.players = players
        self.captains = captains
        self.captain_names = captain_names
        self._normalize_players()
        # 仪式开始时锁定初始起拍价
        for p in self.players:
            p["originalStartPrice"] = max(MIN_BID, int(p.get("startPrice") or MIN_BID))
            p["inUnsoldPool"] = False
            p["excluded"] = False
            p["sold"] = False
            p["finalPrice"] = None
            p["winner"] = None
        for c in self.captains:
            c["team"] = []
        self.phase = "intro"
        self.add_log("公开叫价选人仪式开始", "phase")
        self.add_log("从全部可拍卖选手中按权重随机抽取", "info")
        self.add_log(
            f"每次加价至少 {MIN_INCREMENT}w；加价后 {self.bid_extension_seconds}s 内无人继续加价则落槌",
            "info",
        )
        self.add_log(
            f"若 {self.no_bid_timeout_seconds}s 内尚无人出价则进入流拍池；"
            f"流拍池重拍起拍价为初始价 ×{UNSOLD_PRICE_MULTIPLIER}",
            "info",
        )
        self.add_log("每位队长整场仅可一口价一次；本轮弃权则不再参与该选手拍卖", "info")
        self.add_log("每队每个位置仅可签下一名选手（含队长本人位置）", "info")

    def begin_draw(self) -> None:
        """intro 结束后开始全局抽签（兼容旧 begin_pool_select 调用）。"""
        if self.phase != "intro":
            return
        self.add_log("开始全局抽取拍卖标的", "phase")
        self._start_draw()

    def begin_pool_select(self) -> None:
        """兼容旧 API：改为直接开始全局抽签。"""
        self.begin_draw()

    def select_next_pool(self, pool: str) -> str | None:
        return "已改为全局随机抽签，无需选择位置池"

    def _boost_unsold_prices(self) -> None:
        for p in self.unsold_pool_players():
            original = int(p.get("originalStartPrice") or p.get("startPrice") or MIN_BID)
            boosted = max(MIN_BID, int(round(original * UNSOLD_PRICE_MULTIPLIER)))
            p["startPrice"] = boosted
            p["inUnsoldPool"] = False
        self.auction_stage = "unsold"
        self.add_log(
            f"主池已空 — 流拍池二次拍卖启动（起拍价 = 初始价 ×{UNSOLD_PRICE_MULTIPLIER}）",
            "phase",
        )

    def _finish_ceremony(self) -> None:
        self.phase = "finished"
        self.current_player = None
        self.pending_pick = None
        self.draw_candidates = []
        self.add_log("选人仪式圆满结束", "phase")

    def _weighted_pick(self, pool: list[dict]) -> dict:
        weights = [_player_weight(p) for p in pool]
        return random.choices(pool, weights=weights, k=1)[0]

    def _start_draw(self) -> None:
        drawable = self.drawable_players()
        if not drawable and self.auction_stage == "main" and self.unsold_pool_players():
            # 主池无可抽（或已空），启动流拍池
            self._boost_unsold_prices()
            drawable = self.drawable_players()

        if not drawable:
            # 流拍池里可能还有人但无人可竞拍，或两边都空
            if self.auction_stage == "main" and self.unsold_pool_players():
                self._boost_unsold_prices()
                drawable = self.drawable_players()
            if not drawable:
                # 最后一次尝试：逐个排除确实无人能竞拍的流拍选手
                if self.auction_stage == "unsold":
                    excluded_count = 0
                    remaining_unsold = [
                        p for p in self.players
                        if p.get("inUnsoldPool") and not p.get("sold") and not p.get("excluded")
                    ]
                    for p in remaining_unsold:
                        drawable = self.drawable_players()
                        if drawable:
                            break
                        p["excluded"] = True
                        p["inUnsoldPool"] = False
                        excluded_count += 1
                        self.add_log(f"流拍排除：{p['name']}（无队长可竞拍）", "warn")
                    drawable = self.drawable_players()
                if not drawable:
                    self._finish_ceremony()
                    return

        pick = self._weighted_pick(drawable)
        self.pending_pick = pick
        self.draw_candidates = copy.deepcopy(drawable)
        self.current_player = None
        self.current_pool = pick["position"]
        self.phase = "pool_draw"
        stage_label = "流拍池" if self.auction_stage == "unsold" else "主池"
        self.add_log(
            f"标的抽取 — {stage_label} · {len(drawable)} 名候选",
            "info",
        )

    def reveal_draw(self) -> None:
        if self.phase != "pool_draw" or not self.pending_pick:
            return
        self.current_player = self.pending_pick
        self.pending_pick = None
        self._reshuffle_aliases()
        self.phase = "open_bid"
        self._reset_open_bid_state()
        pos = POSITION_NAMES[self.current_player["position"]]
        start = self._player_start_price()
        buyout = self._player_buyout_price()
        rating = str(self.current_player.get("rating") or "").strip()
        self.add_log(
            f"公开竞拍 — {self.current_player['serial']} {self.current_player['name']} · {pos}"
            + (f" · 评级 {rating}" if rating else ""),
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
        label = self._label(captain_name)
        if action == "pass":
            if not self.captain_can_bid(cap, position) and captain_name not in self.passed_captains:
                reason = self.captain_skip_reason(cap, position)
                return f"不能参与本场竞拍（{reason}）"
            self.passed_captains.add(captain_name)
            self.captain_bids.setdefault(captain_name, None)
            self.add_log(f"[{label}] 放弃本轮竞拍", "info")
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
            self.add_log(f"[{label}] 一口价 {buyout}w！", "buyout")
            cap = next(c for c in self.captains if c["name"] == captain_name)
            self._complete_sale(cap, buyout)
            return None

        if amount < min_next:
            return f"出价须 ≥ {min_next}w"
        if amount > cap["funds"]:
            return "出价超出剩余资金"

        self._record_bid(captain_name, amount)
        self.add_log(f"[{label}] 出价 {amount}w", "bid")
        return None

    def hammer(self) -> str | None:
        if self.phase != "open_bid" or not self.current_player:
            return "当前不能落槌"
        if not self.current_leader or self.current_price <= 0:
            return "尚无人出价，无法落槌"
        cap = next(c for c in self.captains if c["name"] == self.current_leader)
        self.add_log(
            f"管理员落槌 — {self._label(self.current_leader)} · {self.current_price}w",
            "phase",
        )
        self._complete_sale(cap, self.current_price)
        return None

    def _complete_sale(self, cap: dict, price: int) -> None:
        player = next(p for p in self.players if p["serial"] == self.current_player["serial"])
        player["sold"] = True
        player["finalPrice"] = price
        player["winner"] = cap["name"]
        player["inUnsoldPool"] = False
        player["excluded"] = False
        cap["funds"] -= price
        cap["team"].append(player["name"])
        position = player["position"]
        self._show_winner_reveal(player, cap["name"], price)
        self._apply_position_caps(position)

    def _move_to_unsold_pool(self, player: dict) -> None:
        target = next(p for p in self.players if p["serial"] == player["serial"])
        if target.get("sold") or target.get("excluded"):
            return
        target["inUnsoldPool"] = True

    def _show_winner_reveal(self, player: dict, winner: str | None, price: int | None) -> None:
        if winner is None:
            self._move_to_unsold_pool(player)
            player = next(p for p in self.players if p["serial"] == player["serial"])
        self.last_result = {
            "player": copy.deepcopy(player),
            "winner": winner,
            "winnerAlias": self.alias_for(winner) if winner else None,
            "price": price,
        }
        self.current_player = None
        self.phase = "winner_reveal"
        if winner and price is not None:
            self.add_log(
                f"成交：{self._label(winner)} 以 {price}w 签下 {player['name']}",
                "win",
            )
        else:
            self.add_log(f"流拍：{player['name']} — 进入流拍池", "warn")

    def confirm_winner(self) -> None:
        if self.phase != "winner_reveal":
            return
        self.last_result = None
        self.phase = "player_done"
        self._start_draw()


auction = AuctionEngine()
