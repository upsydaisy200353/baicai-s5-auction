"""密码登录与改密 API 测试"""

from fastapi.testclient import TestClient

from auth import hash_password, verify_password
from db import get_user_by_username, init_db, update_user_password
from main import app
from seed_users import default_admin_password, ensure_user_passwords


client = TestClient(app)


def _ensure_admin_password(plain: str = "test-admin-pw") -> None:
    init_db()
    ensure_user_passwords()
    admin = get_user_by_username("admin")
    assert admin is not None
    update_user_password(admin["id"], hash_password(plain))


def test_login_rejects_wrong_password():
    _ensure_admin_password("correct-secret")
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401


def test_login_accepts_correct_password():
    _ensure_admin_password("correct-secret")
    res = client.post(
        "/api/auth/login", json={"username": "admin", "password": "correct-secret"}
    )
    assert res.status_code == 200
    body = res.json()
    assert "token" in body
    assert body["user"]["username"] == "admin"


def test_admin_can_set_and_login_with_new_password():
    _ensure_admin_password("correct-secret")
    login = client.post(
        "/api/auth/login", json={"username": "admin", "password": "correct-secret"}
    )
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    users = client.get("/api/admin/users", headers=headers)
    assert users.status_code == 200
    admin_row = next(u for u in users.json() if u["username"] == "admin")

    set_res = client.put(
        f"/api/admin/users/{admin_row['id']}/password",
        headers=headers,
        json={"newPassword": "brand-new-pw"},
    )
    assert set_res.status_code == 200

    bad = client.post(
        "/api/auth/login", json={"username": "admin", "password": "correct-secret"}
    )
    assert bad.status_code == 401

    good = client.post(
        "/api/auth/login", json={"username": "admin", "password": "brand-new-pw"}
    )
    assert good.status_code == 200


def test_change_own_password():
    _ensure_admin_password("old-pw-123")
    login = client.post(
        "/api/auth/login", json={"username": "admin", "password": "old-pw-123"}
    )
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"currentPassword": "old-pw-123", "newPassword": "new-pw-456"},
    )
    assert res.status_code == 200

    admin = get_user_by_username("admin")
    assert admin is not None
    assert verify_password("new-pw-456", admin["passwordHash"])


def test_default_admin_password_helper():
    assert isinstance(default_admin_password(), str)
    assert len(default_admin_password()) >= 4
