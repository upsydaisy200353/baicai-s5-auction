"""Parse s5_roster.csv into seed row dicts with text rating tiers."""
from __future__ import annotations

import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "data" / "s5_roster.csv"

POS = {
    "上路": "A",
    "打野": "B",
    "中单": "C",
    "下路": "D",
    "辅助": "E",
}


def normalize_tier(raw: str) -> str:
    t = (raw or "").strip().lower()
    if not t:
        return ""
    return t.upper()


def parse_csv_rows() -> list[dict]:
    text = CSV_PATH.read_text(encoding="utf-8-sig")
    rows: list[dict] = []
    serial_n = {L: 0 for L in POS.values()}
    reader = csv.reader(text.splitlines())
    next(reader)
    for cols in reader:
        if len(cols) < 8:
            continue
        nick, game_id, pos, start, buyout, funds, tier = [c.strip() for c in cols[1:8]]
        if not nick or pos not in POS:
            continue
        letter = POS[pos]
        start_i = int(start) if start else 0
        buyout_i = int(buyout) if buyout else None
        funds_i = int(funds) if funds else None
        rating = normalize_tier(tier)
        if funds_i is not None:
            rows.append(
                {
                    "identity": "captain",
                    "name": nick,
                    "poolLetter": letter,
                    "startPrice": start_i,
                    "funds": funds_i,
                    "rating": rating,
                }
            )
        else:
            serial_n[letter] += 1
            rows.append(
                {
                    "identity": "player",
                    "serial": f"{letter}{serial_n[letter]}",
                    "name": game_id or nick,
                    "poolLetter": letter,
                    "startPrice": start_i,
                    "buyoutPrice": buyout_i or 0,
                    "rating": rating,
                    "weight": 1,
                }
            )
    return rows
