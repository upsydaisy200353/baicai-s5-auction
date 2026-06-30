#!/usr/bin/env python3
"""白菜 S5 选手拍卖 Demo"""

import random
import sys

from auction import BidAction, MIN_INCREMENT, MAX_INCREMENT, create_state
from data import CAPTAINS, PLAYERS, POSITION_NAMES


def print_banner() -> None:
    print("=" * 56)
    print("       白菜 S5 选手拍卖系统 — Demo")
    print("=" * 56)
    print("\n规则摘要：")
    print("  1. 位置池(上/野/中/下/辅)由弱队长优先选择顺序")
    print("  2. 每池随机抽取选手逐个拍卖")
    print("  3. 首轮：实力强→弱出价；后续轮：资金少→多出价")
    print("  4. 加价幅度 10w~100w，且不得低于上一轮幅度")
    print("  5. 完整一轮无人加价则当前最高价成交")
    print("  6. 一口价仅首轮可用")
    print()


def print_roster() -> None:
    print("--- 队长名单 ---")
    for c in sorted(CAPTAINS, key=lambda x: -x.rating):
        print(f"  {c.name:8s}  实力{c.rating:4d}  资金{c.funds}w")

    print("\n--- 选手名单（按位置） ---")
    for pos, cn in POSITION_NAMES.items():
        group = [p for p in PLAYERS if p.position == pos]
        print(f"\n  [{cn}]")
        for p in group:
            print(f"    {p.serial} {p.name:16s}  起拍{p.start_price}w  一口价{p.buyout_price}w")


def manual_bid_callback(cap, state, round_num, current_price, last_increment, is_first):
    """交互式出价（指定某队长时使用）"""
    print(
        f"\n  >> {cap.name} 的回合 (剩余{cap.remaining}w, 当前价{current_price}w, "
        f"最低加{max(last_increment, MIN_INCREMENT)}w)"
    )
    if is_first:
        print("     [b] 加价  [o] 一口价  [p] 放弃")
    else:
        print("     [b] 加价  [p] 放弃")

    try:
        choice = input("     请选择: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return None

    if choice == "p" or choice == "":
        return None
    if choice == "o" and is_first:
        player_buyout = current_price  # placeholder; real buyout handled in engine
        return BidAction(cap.name, "buyout")
    if choice == "b":
        try:
            inc = int(input(f"     加价幅度 ({MIN_INCREMENT}-{MAX_INCREMENT}w): "))
        except ValueError:
            return None
        return BidAction(cap.name, "bid", increment=inc)
    return None


def run_auto_demo(seed: int | None = None, *, verbose: bool = False) -> None:
    if seed is not None:
        random.seed(seed)
    state = create_state(verbose=verbose)
    state.run_full_auction()


def run_interactive_demo() -> None:
    print("\n交互模式：每轮拍卖时你扮演所有队长，依次输入出价。")
    print("（输入 p 放弃，b 加价，首轮可用 o 一口价）\n")
    state = create_state(verbose=True)
    state.run_full_auction(bid_callback=manual_bid_callback)


def main() -> None:
    print_banner()

    if len(sys.argv) > 1 and sys.argv[1] == "roster":
        print_roster()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        print_roster()
        run_interactive_demo()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "verbose":
        seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
        print(f"详细日志模式 (seed={seed})\n")
        print_roster()
        print()
        run_auto_demo(seed, verbose=True)
        return

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    print(f"自动模拟模式 (seed={seed})")
    print("  `python main.py interactive` — 交互出价")
    print("  `python main.py verbose [seed]` — 详细日志\n")
    print_roster()
    print()
    run_auto_demo(seed)


if __name__ == "__main__":
    main()
