"""FastAPI — 名单 / 认证 / 多人拍卖"""

from __future__ import annotations

from typing import Literal

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from auth import (
    create_token,
    get_current_user,
    get_optional_user,
    require_admin,
    require_captain_or_admin,
)
from auction_engine import auction
from constants import POOL_LETTERS, POSITION_NAMES, POSITION_TO_LETTER
from db import (
    DB_PATH,
    create_entry,
    delete_entry,
    get_entry,
    get_storage_backend,
    get_user_by_username,
    init_db,
    list_roster,
    update_entry,
)
from seed import reseed, seed_if_empty
from seed_users import seed_users

app = FastAPI(title="白菜杯拍卖 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=64)


class RosterPayload(BaseModel):
    sortOrder: int | None = None
    identity: Literal["player", "captain"]
    serial: str | None = None
    name: str = Field(min_length=1, max_length=64)
    poolLetter: Literal["A", "B", "C", "D", "E"] | None = None
    position: Literal["Top", "Jungle", "Mid", "Bot", "Support"] | None = None
    startPrice: int = Field(ge=0, default=0)
    buyoutPrice: int | None = Field(default=None, ge=0)
    funds: int | None = Field(default=None, ge=0)
    avatar: str | None = None

    @model_validator(mode="after")
    def resolve_pool(self):
        if self.poolLetter is None and self.position is not None:
            self.poolLetter = POSITION_TO_LETTER[self.position]
        if self.position is None and self.poolLetter is not None:
            self.position = POOL_LETTERS[self.poolLetter]
        if self.poolLetter is None:
            raise ValueError("poolLetter 或 position 必须提供其一")
        if self.identity == "captain" and self.funds is None:
            raise ValueError("队长必须填写竞拍资金 funds")
        return self


class PoolSelectPayload(BaseModel):
    pool: Literal["Top", "Jungle", "Mid", "Bot", "Support"]


class OpenBidPayload(BaseModel):
    action: Literal["bid", "pass", "buyout"]
    amount: int | None = Field(default=None, ge=1)
    captainName: str | None = None


class AuctionSettingsPayload(BaseModel):
    bidExtensionSeconds: int = Field(ge=5, le=300)
    noBidTimeoutSeconds: int = Field(ge=10, le=600)


def entries_to_auction_data(entries: list[dict]) -> dict:
    players = []
    captains = []
    for e in entries:
        if e["identity"] == "captain":
            captains.append(
                {
                    "name": e["name"],
                    "rating": e["startPrice"],
                    "funds": e["funds"],
                    "poolLetter": e["poolLetter"],
                    "avatar": e.get("avatar"),
                    "team": [],
                }
            )
        else:
            players.append(
                {
                    "serial": e["serial"] or "",
                    "name": e["name"],
                    "startPrice": e.get("startPrice") or 0,
                    "buyoutPrice": e.get("buyoutPrice") or 0,
                    "position": e["position"],
                    "avatar": e.get("avatar"),
                    "sold": False,
                    "finalPrice": None,
                    "winner": None,
                }
            )
    return {"entries": entries, "players": players, "captains": captains}


def _avatar_map() -> dict[str, str | None]:
    return {
        e["serial"]: e.get("avatar")
        for e in list_roster()
        if e["identity"] == "player" and e.get("serial")
    }


def _captain_avatar_map() -> dict[str, str | None]:
    return {
        e["name"]: e.get("avatar")
        for e in list_roster()
        if e["identity"] == "captain"
    }


def _apply_avatar(player: dict | None, avatars: dict[str, str | None]) -> None:
    if not player:
        return
    serial = player.get("serial")
    if serial and serial in avatars:
        player["avatar"] = avatars[serial]


def enrich_auction_state(state: dict) -> dict:
    """拍卖进行中内存里的选手/队长可能缺少 avatar，从名单库补全。"""
    avatars = _avatar_map()
    cap_avatars = _captain_avatar_map()
    for p in state.get("players", []):
        _apply_avatar(p, avatars)
    for c in state.get("captains", []):
        name = c.get("name")
        if name and name in cap_avatars:
            c["avatar"] = cap_avatars[name]
    _apply_avatar(state.get("currentPlayer"), avatars)
    for ctx_key in ("openBid", "playerReveal"):
        ctx = state.get(ctx_key)
        if ctx and ctx.get("player"):
            _apply_avatar(ctx["player"], avatars)
    for p in state.get("drawCandidates", []):
        _apply_avatar(p, avatars)
    if state.get("lastResult") and state["lastResult"].get("player"):
        _apply_avatar(state["lastResult"]["player"], avatars)
    return state


def _mask_funds_for_viewer(state: dict, viewer_captain: str | None, is_admin: bool) -> dict:
    """管理员可见全部资金；队长仅可见自己；观战隐藏全部。"""
    if is_admin:
        return state

    def mask_captain_list(captains: list[dict]) -> None:
        for c in captains:
            if c.get("name") != viewer_captain:
                c["funds"] = None

    def mask_captain_rows(rows: list[dict]) -> None:
        for row in rows:
            if row.get("name") != viewer_captain:
                row["funds"] = None

    mask_captain_list(state.get("captains", []))
    open_bid = state.get("openBid")
    if open_bid:
        mask_captain_rows(open_bid.get("captainRows", []))
        mask_captain_list(open_bid.get("eligibleCaptains", []))
    return state


def auction_state_response(user: dict | None = None) -> dict:
    state = enrich_auction_state(auction.to_state())
    is_admin = bool(user and user.get("role") == "admin")
    viewer_captain = user.get("captainName") if user and user.get("role") == "captain" else None
    return _mask_funds_for_viewer(state, viewer_captain, is_admin)


def load_auction_from_db() -> None:
    data = entries_to_auction_data(list_roster())
    auction.load_roster(data["players"], data["captains"])


@app.on_event("startup")
def startup():
    init_db()
    backend = get_storage_backend()
    print(f"Storage: {'PostgreSQL (DATABASE_URL)' if backend == 'postgres' else f'SQLite ({DB_PATH})'}")
    seed_if_empty()
    seed_users()
    try:
        from assign_avatars import assign_player_avatars, ensure_avatar_db_paths

        if assign_player_avatars() == 0:
            ensure_avatar_db_paths()
    except Exception:
        pass
    load_auction_from_db()


# ── 认证 ──────────────────────────────────────────

@app.post("/api/auth/login")
def login(payload: LoginPayload):
    user = get_user_by_username(payload.username.strip())
    if not user:
        raise HTTPException(401, "用户不存在")
    token = create_token(user)
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "captainName": user.get("captainName"),
            "displayName": user.get("displayName"),
        },
    }


@app.get("/api/auth/me")
def me(user: dict = Depends(get_current_user)):
    return user


@app.get("/api/auth/accounts-hint")
def accounts_hint():
    """可选登录身份（免密，仅供前端展示）"""
    return {
        "admin": {"username": "admin", "displayName": "管理员", "role": "admin"},
        "captains": [
            {"username": username, "displayName": name}
            for username, name in [
                ("wuyanzu", "吴彦祖"),
                ("yazi", "亚子"),
                ("caps", "caps"),
                ("baiweiyi", "白惟一"),
                ("mushroom", "🍄"),
                ("xxts", "xxts"),
                ("yume", "Yume"),
                ("pika", "皮卡"),
            ]
        ],
    }


# ── 元数据 / 名单（读公开，写需管理员）──────────────

@app.get("/api/meta")
def meta():
    backend = get_storage_backend()
    return {
        "poolLetters": POOL_LETTERS,
        "positionNames": POSITION_NAMES,
        "positionToLetter": POSITION_TO_LETTER,
        "storage": backend,
        "storagePersistent": backend == "postgres",
    }


@app.get("/api/roster")
def get_roster(_user: dict | None = Depends(get_optional_user)):
    entries = list_roster()
    return entries_to_auction_data(entries)


@app.get("/api/roster/entries")
def get_entries(_user: dict = Depends(require_admin)):
    return list_roster()


@app.get("/api/roster/entries/{entry_id}")
def get_one(entry_id: int, _user: dict = Depends(require_admin)):
    entry = get_entry(entry_id)
    if not entry:
        raise HTTPException(404, "记录不存在")
    return entry


@app.post("/api/roster/entries")
def create_one(payload: RosterPayload, _user: dict = Depends(require_admin)):
    data = payload.model_dump()
    entry = create_entry(data)
    load_auction_from_db()
    return entry


@app.put("/api/roster/entries/{entry_id}")
def update_one(entry_id: int, payload: RosterPayload, _user: dict = Depends(require_admin)):
    existing = get_entry(entry_id)
    if not existing:
        raise HTTPException(404, "记录不存在")
    data = {**existing, **payload.model_dump()}
    entry = update_entry(entry_id, data)
    load_auction_from_db()
    return entry


@app.delete("/api/roster/entries/{entry_id}")
def remove_one(entry_id: int, _user: dict = Depends(require_admin)):
    if not delete_entry(entry_id):
        raise HTTPException(404, "记录不存在")
    load_auction_from_db()
    return {"ok": True}


@app.post("/api/roster/reseed")
def reset_roster(_user: dict = Depends(require_admin)):
    reseed()
    entries = list_roster()
    load_auction_from_db()
    return entries_to_auction_data(entries)


# ── 多人拍卖 ──────────────────────────────────────

@app.get("/api/auction/state")
def auction_state(user: dict = Depends(get_current_user)):
    return auction_state_response(user)


@app.get("/api/auction/spectator")
def auction_spectator():
    """观战大屏只读状态，无需登录"""
    return auction_state_response()


@app.post("/api/auction/start")
def auction_start(_user: dict = Depends(require_admin)):
    load_auction_from_db()
    auction.start()
    return auction_state_response(_user)


@app.post("/api/auction/begin")
def auction_begin(_user: dict = Depends(require_admin)):
    auction.begin_pool_select()
    return auction_state_response(_user)


@app.post("/api/auction/select-pool")
def auction_select_pool(
    payload: PoolSelectPayload,
    _user: dict = Depends(require_admin),
):
    err = auction.select_next_pool(payload.pool)
    if err:
        raise HTTPException(400, err)
    return auction_state_response(_user)


@app.post("/api/auction/reveal-draw")
def auction_reveal_draw(_user: dict = Depends(require_admin)):
    auction.reveal_draw()
    return auction_state_response(_user)


@app.post("/api/auction/hammer")
def auction_hammer(_user: dict = Depends(require_admin)):
    err = auction.hammer()
    if err:
        raise HTTPException(400, err)
    return auction_state_response(_user)


@app.post("/api/auction/confirm-winner")
def auction_confirm_winner(_user: dict = Depends(require_admin)):
    auction.confirm_winner()
    return auction_state_response(_user)


@app.post("/api/auction/bid")
def auction_bid(payload: OpenBidPayload, user: dict = Depends(require_captain_or_admin)):
    if auction.phase != "open_bid":
        raise HTTPException(400, "当前不在公开叫价阶段")

    if user["role"] == "admin":
        captain_name = payload.captainName
        if not captain_name:
            raise HTTPException(400, "管理员代投须指定 captainName")
        valid_names = {c["name"] for c in auction.captains}
        if captain_name not in valid_names:
            raise HTTPException(400, "队长不存在")
    else:
        captain_name = user.get("captainName")
        if not captain_name:
            raise HTTPException(403, "非队长账号")

    err = auction.submit_open_bid(
        captain_name,
        payload.action,
        amount=payload.amount,
    )
    if err:
        raise HTTPException(400, err)
    return auction_state_response(user)


@app.post("/api/auction/settings")
def auction_settings(
    payload: AuctionSettingsPayload,
    _user: dict = Depends(require_admin),
):
    auction.set_timing(payload.bidExtensionSeconds, payload.noBidTimeoutSeconds)
    return auction_state_response(_user)


@app.post("/api/auction/reset")
def auction_reset(_user: dict = Depends(require_admin)):
    load_auction_from_db()
    auction.reset()
    return auction_state_response(_user)


FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def _mount_frontend() -> None:
    if not FRONTEND_DIST.is_dir():
        return
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not Found")
        target = FRONTEND_DIST / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(FRONTEND_DIST / "index.html")


_mount_frontend()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
