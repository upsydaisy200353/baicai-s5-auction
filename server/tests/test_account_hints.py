"""登录页账号列表应只含名单中的现任队长"""

from fastapi.testclient import TestClient

from db import clear_roster, create_entry, create_user, init_db, list_roster
from auth import hash_password
from main import app
from seed_users import list_account_hints


client = TestClient(app)


def test_account_hints_only_roster_captains():
    init_db()
    # 制造一个「旧队长」账号，但不在当前名单
    from db import get_user_by_username

    orphan_name = "orphan_cap_test_hints"
    if not get_user_by_username(orphan_name):
        create_user(
            {
                "username": orphan_name,
                "passwordHash": hash_password("x"),
                "passwordPlain": "x",
                "role": "captain",
                "captainName": "已淘汰队长",
                "displayName": "已淘汰队长",
            }
        )
    roster_names = {e["name"] for e in list_roster() if e["identity"] == "captain"}
    assert "已淘汰队长" not in roster_names

    hints = list_account_hints()
    hint_names = {c["displayName"] for c in hints["captains"]}
    assert "已淘汰队长" not in hint_names
    assert hint_names == roster_names
    assert hints["captainCount"] == len(roster_names)

    api = client.get("/api/auth/accounts-hint")
    assert api.status_code == 200
    body = api.json()
    assert {c["displayName"] for c in body["captains"]} == roster_names
