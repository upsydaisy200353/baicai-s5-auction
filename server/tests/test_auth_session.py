"""单账号单会话：仅队长生效，管理员可多端同时在线"""

from auth import create_token, decode_token
from db import bump_user_session_version, get_user_by_username, init_db, list_users


def _captain_user():
    for user in list_users():
        if user["role"] == "captain":
            return user
    return None


def test_captain_new_login_invalidates_old_token():
    init_db()
    user = _captain_user()
    assert user is not None

    old_sv = bump_user_session_version(user["id"])
    old_token = create_token(user, old_sv)

    new_sv = bump_user_session_version(user["id"])
    assert new_sv == old_sv + 1

    user = get_user_by_username(user["username"])
    assert user is not None
    assert user["sessionVersion"] == new_sv

    payload = decode_token(old_token)
    assert int(payload["sv"]) != user["sessionVersion"]


def test_admin_login_does_not_bump_session_version():
    init_db()
    admin = get_user_by_username("admin")
    assert admin is not None

    before = int(admin["sessionVersion"])
    after_sv = before
    token = create_token(admin, after_sv)

    admin = get_user_by_username("admin")
    assert admin is not None
    assert admin["sessionVersion"] == before

    payload = decode_token(token)
    assert int(payload["sv"]) == before
