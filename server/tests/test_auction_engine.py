"""拍卖引擎核心规则测试"""

from auction_engine import AuctionEngine


def _sample_roster():
    players = [
        {
            "serial": "E1",
            "name": "选手A",
            "startPrice": 100,
            "buyoutPrice": 500,
            "position": "Support",
            "sold": False,
            "finalPrice": None,
            "winner": None,
        },
        {
            "serial": "E2",
            "name": "选手B",
            "startPrice": 120,
            "buyoutPrice": 600,
            "position": "Support",
            "sold": False,
            "finalPrice": None,
            "winner": None,
        },
    ]
    captains = [
        {
            "name": "队长甲",
            "rating": 100,
            "funds": 1000,
            "poolLetter": "A",
            "team": [],
        },
        {
            "name": "队长乙",
            "rating": 100,
            "funds": 1000,
            "poolLetter": "B",
            "team": [],
        },
    ]
    return players, captains


def _open_bid(engine, player):
    engine.phase = "open_bid"
    engine.current_player = player
    engine._reset_open_bid_state()


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


def test_all_passed_early_flow():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    _open_bid(engine, players[0])

    assert engine.submit_open_bid("队长甲", "pass") is None
    assert engine.submit_open_bid("队长乙", "pass") is None
    engine._check_all_passed_early()
    assert engine.phase == "winner_reveal"
    assert engine.last_result["winner"] is None


def test_serialize_roundtrip():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    engine.start()
    engine.used_buyout.add("队长甲")
    raw = engine.serialize()

    other = AuctionEngine()
    other.deserialize(raw)
    assert other.phase == engine.phase
    assert other.used_buyout == engine.used_buyout
    assert other.players[0]["name"] == "选手A"


def test_reset_ceremony_keeps_roster():
    engine = AuctionEngine()
    players, captains = _sample_roster()
    engine.load_roster(players, captains)
    engine.start()
    engine.reset_ceremony()
    assert engine.phase == "idle"
    assert len(engine.players) == 2
    assert len(engine.captains) == 2
