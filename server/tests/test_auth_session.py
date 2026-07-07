"""单账号单会话：新登录会使旧 token 失效"""

from auth import create_token, decode_token
from db import bump_user_session_version, get_user_by_username, init_db


def test_new_login_invalidates_old_token():
    init_db()
    user = get_user_by_username("admin")
    assert user is not None

    old_sv = bump_user_session_version(user["id"])
    old_token = create_token(user, old_sv)

    new_sv = bump_user_session_version(user["id"])
    assert new_sv == old_sv + 1

    user = get_user_by_username("admin")
    assert user is not None
    assert user["sessionVersion"] == new_sv

    payload = decode_token(old_token)
    assert int(payload["sv"]) != user["sessionVersion"]
