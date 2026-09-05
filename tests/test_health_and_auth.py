import pytest
from app.core.security import create_password_reset_token


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_auth_token_username_password_success(client):
    # Standard 1.2: POST /v1/auth/token with username and password
    response = await client.post(
        "/v1/auth/token",
        json={
            "grant_type": "password",
            "username": "test@s247.local",
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"].lower() == "bearer"
    assert data["expires_in"] > 0

    token = data["access_token"]

    # Test /v1/me with token
    me_resp = await client.get(
        "/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "test@s247.local"
    assert me_data["role"] == "admin"


@pytest.mark.asyncio
async def test_auth_token_refresh_rotation(client):
    # 1. Login to get initial token pair
    login_resp = await client.post(
        "/v1/auth/token",
        json={"username": "test@s247.local", "password": "testpass123"},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    old_refresh = tokens["refresh_token"]

    # 2. Call /v1/auth/token/refresh
    refresh_resp = await client.post(
        "/v1/auth/token/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != old_refresh

    # 3. Legitimate second refresh with new_tokens succeeds
    second_refresh_resp = await client.post(
        "/v1/auth/token/refresh",
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    assert second_refresh_resp.status_code == 200
    third_tokens = second_refresh_resp.json()
    assert third_tokens["refresh_token"] != new_tokens["refresh_token"]

    # 4. Attempting to reuse an already-rotated token (old_refresh) triggers RTR breach detection
    reuse_resp = await client.post(
        "/v1/auth/token/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reuse_resp.status_code == 401

    # 5. Due to RTR breach detection, the entire active token family for this user is revoked
    invalidated_resp = await client.post(
        "/v1/auth/token/refresh",
        json={"refresh_token": third_tokens["refresh_token"]},
    )
    assert invalidated_resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_token_grant_type_refresh(client):
    # Standard OAuth2: POST /v1/auth/token with grant_type=refresh_token
    login_resp = await client.post(
        "/v1/auth/token",
        json={"username": "test@s247.local", "password": "testpass123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    grant_resp = await client.post(
        "/v1/auth/token",
        json={"grant_type": "refresh_token", "refresh_token": refresh_token},
    )
    assert grant_resp.status_code == 200
    data = grant_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_auth_logout_revocation(client):
    login_resp = await client.post(
        "/v1/auth/token",
        json={"username": "test@s247.local", "password": "testpass123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Call logout
    logout_resp = await client.post(
        "/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 200

    # Refresh token should now be revoked
    refresh_resp = await client.post(
        "/v1/auth/token/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401

    # Also test DELETE /v1/auth/token
    login2 = await client.post(
        "/v1/auth/token",
        json={"username": "test@s247.local", "password": "testpass123"},
    )
    refresh2 = login2.json()["refresh_token"]
    del_resp = await client.request(
        "DELETE",
        "/v1/auth/token",
        json={"refresh_token": refresh2},
    )
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_auth_unauthorized_header(client):
    # Invalid password triggers 401 with WWW-Authenticate header
    response = await client.post(
        "/v1/auth/token",
        json={"username": "test@s247.local", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "www-authenticate" in response.headers
    assert "Bearer" in response.headers["www-authenticate"]

    # Missing token on protected endpoint triggers 401 with WWW-Authenticate header
    me_resp = await client.get("/v1/me")
    assert me_resp.status_code == 401
    assert "www-authenticate" in me_resp.headers


@pytest.mark.asyncio
async def test_auth_register_and_login(client):
    # 1. Register new user
    reg_resp = await client.post(
        "/v1/auth/register",
        json={
            "email": "newuser@s247.local",
            "password": "strongPassword123",
            "full_name": "Nowy Użytkownik",
        },
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["email"] == "newuser@s247.local"
    assert reg_data["role"] == "client"

    # 2. Login with registered credentials
    login_resp = await client.post(
        "/v1/auth/token",
        json={"username": "newuser@s247.local", "password": "strongPassword123"},
    )
    assert login_resp.status_code == 200

    # 3. Duplicate email causes 409 Conflict
    dup_resp = await client.post(
        "/v1/auth/register",
        json={
            "email": "newuser@s247.local",
            "password": "strongPassword123",
            "full_name": "Another User",
        },
    )
    assert dup_resp.status_code == 409


@pytest.mark.asyncio
async def test_auth_password_forgot_and_reset(client, db_session):
    # 1. Forgot password request
    forgot_resp = await client.post(
        "/v1/auth/password/forgot",
        json={"email": "test@s247.local"},
    )
    assert forgot_resp.status_code == 200

    # 2. Create valid reset token for test user (id=1)
    reset_token = create_password_reset_token(1, "test@s247.local")

    # 3. Reset password
    reset_resp = await client.post(
        "/v1/auth/password/reset",
        json={"token": reset_token, "new_password": "NewSecretPassword123"},
    )
    assert reset_resp.status_code == 200

    # 4. Old password fails
    old_login = await client.post(
        "/v1/auth/token",
        json={"username": "test@s247.local", "password": "testpass123"},
    )
    assert old_login.status_code == 401

    # 5. New password succeeds
    new_login = await client.post(
        "/v1/auth/token",
        json={"username": "test@s247.local", "password": "NewSecretPassword123"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_legacy_aliases(client):
    # /v1/auth/login alias
    login_resp = await client.post(
        "/v1/auth/login",
        json={"email": "test@s247.local", "password": "testpass123"},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    # /v1/auth/refresh alias
    ref_resp = await client.post(
        "/v1/auth/refresh",
        json={"token": refresh_token},
    )
    assert ref_resp.status_code == 200
