"""拍卖引擎核心规则测试"""

import random

from auction_engine import (
    DEFAULT_BID_EXTENSION_SECONDS,
    UNSOLD_PRICE_MULTIPLIER,
    AuctionEngine,
)


def _player(
    serial: str,
    name: str,
    position: str,
    *,
    start: int = 100,
    buyout: int = 500,
    rating: str = "UR",
    weight: int = 1,
):
    return {
        "serial": serial,
        "name": name,
        "startPrice": start,
        "originalStartPrice": start,
        "buyoutPrice": buyout,
        "rating": rating,
        "weight": weight,
        "position": position,
        "sold": False,
        "inUnsoldPool": False,
        "excluded": False,
        "finalPrice": None,
        "winner": None,
    }


def _captain(name: str, pool_letter: str, funds: int = 5000):
    return {
        "name": name,
        "rating": 100,
        "funds": funds,
        "poolLetter": pool_letter,
        "team": [],
    }


def _sample_roster():
    players = [
        _player("E1", "选手A", "Support", start=100, buyout=500),
        _player("E2", "选手B", "Support", start=120, buyout=600),
    ]
    captains = [
        _captain("队长甲", "A"),
        _captain("队长乙", "B"),
    ]
    return players, captains


def _open_bid(engine, player):
    engine.phase = "open_bid"
    engine.current_player = player
    engine._reshuffle_aliases()
    engine._reset_open_bid_state()


def test_default_bid_extension_is_30():
    assert DEFAULT_BID_EXTENSION_SECONDS == 30
    engine = AuctionEngine()
    assert engine.bid_extension_seconds == 30


def test_min_increment_is_10():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    _open_bid(engine, players[0])

    assert engine.submit_open_bid("队长甲", "bid", amount=100) is None

    err = engine.submit_open_bid("队长乙", "bid", amount=105)
    assert err is not None

    err = engine.submit_open_bid("队长乙", "bid", amount=110)
    assert err is None
    assert engine.current_price == 110


def test_buyout_once_per_ceremony():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    engine.start()
    _open_bid(engine, players[0])

    engine.used_buyout.add("队长甲")
    err = engine.submit_open_bid("队长甲", "buyout", amount=500)
    assert err is not None
    assert "一口价" in err


def test_pass_locks_out_for_lot():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    _open_bid(engine, players[0])

    assert engine.submit_open_bid("队长甲", "pass") is None
    err = engine.submit_open_bid("队长甲", "bid", amount=100)
    assert err is not None


def test_all_passed_goes_to_unsold_pool():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    _open_bid(engine, players[0])

    assert engine.submit_open_bid("队长甲", "pass") is None
    assert engine.submit_open_bid("队长乙", "pass") is None
    engine._check_all_passed_early()
    assert engine.phase == "winner_reveal"
    assert engine.last_result["winner"] is None
    target = next(p for p in engine.players if p["serial"] == "E1")
    assert target["inUnsoldPool"] is True
    assert target["sold"] is False
    assert target not in engine.main_pool_players()
    assert target in engine.unsold_pool_players()


def test_weighted_pick_prefers_higher_weight():
    engine = AuctionEngine()
    players = [
        _player("A1", "低权重", "Top", weight=1),
        _player("A2", "高权重", "Top", weight=10_000),
    ]
    captains = [_captain("队长甲", "B"), _captain("队长乙", "C")]
    engine.load_roster(players, captains)

    random.seed(42)
    picks = [engine._weighted_pick(players)["serial"] for _ in range(40)]
    assert picks.count("A2") > picks.count("A1")


def test_global_draw_picks_across_positions():
    engine = AuctionEngine()
    players = [
        _player("A1", "上单甲", "Top"),
        _player("C1", "中单甲", "Mid"),
    ]
    captains = [_captain("队长甲", "B"), _captain("队长乙", "E")]
    engine.load_roster(players, captains)
    engine.start()
    engine.begin_draw()
    assert engine.phase == "pool_draw"
    assert engine.pending_pick is not None
    assert engine.pending_pick["serial"] in {"A1", "C1"}
    assert len(engine.draw_candidates) == 2


def test_soft_cap_moves_remaining_to_unsold():
    """n=1 上单队长 → soft=6：第 6 名成交后其余进流拍池。"""
    engine = AuctionEngine()
    players = [_player(f"A{i}", f"上单{i}", "Top") for i in range(1, 9)]
    captains = [
        _captain("上单队长", "A"),
        _captain("打野队长", "B"),
        _captain("中单队长", "C"),
    ]
    engine.load_roster(players, captains)
    # 模拟已成交 5 人
    for i in range(5):
        engine.players[i]["sold"] = True
        engine.players[i]["winner"] = "打野队长"
        engine.captains[1]["team"].append(engine.players[i]["name"])
    # 第 6 成交触发 soft
    engine.current_player = engine.players[5]
    engine._complete_sale(engine.captains[1], 100)
    remaining = [p for p in engine.players if not p["sold"]]
    assert all(p["inUnsoldPool"] for p in remaining)
    assert not any(p["excluded"] for p in remaining)


def test_hard_cap_excludes_remaining():
    """n=1 → hard=7：第 7 名成交后其余消失。"""
    engine = AuctionEngine()
    players = [_player(f"A{i}", f"上单{i}", "Top") for i in range(1, 10)]
    captains = [
        _captain("上单队长", "A"),
        _captain("打野队长", "B"),
        _captain("中单队长", "C"),
        _captain("下路队长", "D"),
    ]
    engine.load_roster(players, captains)
    for i in range(6):
        engine.players[i]["sold"] = True
        engine.players[i]["winner"] = "打野队长"
    engine.current_player = engine.players[6]
    engine._complete_sale(engine.captains[1], 100)
    remaining = [p for p in engine.players if not p["sold"]]
    assert all(p["excluded"] for p in remaining)
    assert not any(p["inUnsoldPool"] for p in remaining)


def test_unsold_reauction_boosts_start_price_once():
    engine = AuctionEngine()
    players = [
        _player("A1", "流拍甲", "Top", start=100),
        _player("C1", "流拍乙", "Mid", start=200),
    ]
    captains = [_captain("队长甲", "B"), _captain("队长乙", "E")]
    engine.load_roster(players, captains)
    for p in engine.players:
        p["inUnsoldPool"] = True
    engine.auction_stage = "main"
    engine._boost_unsold_prices()
    assert engine.auction_stage == "unsold"
    assert engine.players[0]["startPrice"] == int(round(100 * UNSOLD_PRICE_MULTIPLIER))
    assert engine.players[1]["startPrice"] == int(round(200 * UNSOLD_PRICE_MULTIPLIER))
    assert all(not p["inUnsoldPool"] for p in engine.players)

    # 再次流拍再 boost：相对 original，不叠乘
    for p in engine.players:
        p["inUnsoldPool"] = True
    engine._boost_unsold_prices()
    assert engine.players[0]["startPrice"] == int(round(100 * UNSOLD_PRICE_MULTIPLIER))
    assert engine.players[1]["startPrice"] == int(round(200 * UNSOLD_PRICE_MULTIPLIER))


def test_alias_reshuffle_unique_per_round():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    engine._reshuffle_aliases()
    first = dict(engine.captain_aliases)
    assert len(first) == 2
    assert len(set(first.values())) == 2
    engine._reshuffle_aliases()
    second = dict(engine.captain_aliases)
    assert len(set(second.values())) == 2
    # 可能偶然相同，至少结构正确
    assert set(second.keys()) == {"队长甲", "队长乙"}


def test_reveal_draw_assigns_aliases():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    engine.start()
    engine.begin_draw()
    engine.reveal_draw()
    assert engine.phase == "open_bid"
    assert len(engine.captain_aliases) == 2
    assert engine.alias_for("队长甲") is not None


def test_serialize_roundtrip():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    engine.start()
    engine.used_buyout.add("队长甲")
    engine.captain_aliases = {"队长甲": "锋喙鸟", "队长乙": "暗影狼"}
    raw = engine.serialize()

    other = AuctionEngine()
    other.deserialize(raw)
    assert other.phase == engine.phase
    assert other.used_buyout == engine.used_buyout
    assert other.players[0]["name"] == "选手A"
    assert other.captain_aliases["队长甲"] == "锋喙鸟"
    assert other.bid_extension_seconds == 30


def test_reset_ceremony_keeps_roster():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    engine.start()
    engine.reset_ceremony()
    assert engine.phase == "idle"
    assert len(engine.players) == 2
    assert len(engine.captains) == 2
