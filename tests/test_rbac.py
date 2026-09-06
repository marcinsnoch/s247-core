import pytest
from app.core.rbac import Permission


async def get_token_for(client, username, password):
    resp = await client.post(
        "/v1/auth/token",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_admin_full_access(client):
    admin_token = await get_token_for(client, "test@s247.local", "testpass123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Admin can list users
    users_resp = await client.get("/v1/users/", headers=headers)
    assert users_resp.status_code == 200

    # 2. Admin can create user
    create_user_resp = await client.post(
        "/v1/users/",
        headers=headers,
        json={
            "email": "createdbyadmin@s247.local",
            "password": "Password123!",
            "full_name": "Created By Admin",
            "role": "client",
        },
    )
    assert create_user_resp.status_code == 201

    # 3. Admin can create workspace
    create_ws_resp = await client.post(
        "/v1/workspaces/",
        headers=headers,
        json={"code": "WS0099", "name": "New Admin Tenant"},
    )
    assert create_ws_resp.status_code == 201

    # 4. Admin can register device
    ws_id = create_ws_resp.json()["id"]
    create_dev_resp = await client.post(
        "/v1/devices/",
        headers=headers,
        json={"code": "DEV-001", "name": "Laser Cutter X1", "workspace_id": ws_id},
    )
    assert create_dev_resp.status_code == 201


@pytest.mark.asyncio
async def test_technician_rbac_permissions(client):
    tech_token = await get_token_for(client, "tech@s247.local", "techpass123")
    headers = {"Authorization": f"Bearer {tech_token}"}

    # 1. Technician can view users (users:read)
    users_resp = await client.get("/v1/users/", headers=headers)
    assert users_resp.status_code == 200

    # 2. Technician CANNOT create users (missing users:create) -> 403 Forbidden
    create_user_resp = await client.post(
        "/v1/users/",
        headers=headers,
        json={
            "email": "failby_tech@s247.local",
            "password": "Password123!",
            "full_name": "Failed User",
            "role": "client",
        },
    )
    assert create_user_resp.status_code == 403
    err = create_user_resp.json()["error"]
    assert err["code"] == "FORBIDDEN"

    # 3. Technician can view workspaces (workspaces:read)
    ws_resp = await client.get("/v1/workspaces/", headers=headers)
    assert ws_resp.status_code == 200

    # 4. Technician CANNOT create workspaces (missing workspaces:create) -> 403 Forbidden
    create_ws_resp = await client.post(
        "/v1/workspaces/",
        headers=headers,
        json={"code": "WS0098", "name": "Tech Tenant"},
    )
    assert create_ws_resp.status_code == 403

    # 5. Technician can register devices (devices:create)
    create_dev_resp = await client.post(
        "/v1/devices/",
        headers=headers,
        json={"code": "DEV-TECH-01", "name": "CNC Mill T1", "workspace_id": 1},
    )
    assert create_dev_resp.status_code == 201


@pytest.mark.asyncio
async def test_client_rbac_permissions(client):
    client_token = await get_token_for(client, "client@s247.local", "clientpass123")
    headers = {"Authorization": f"Bearer {client_token}"}

    # 1. Client CANNOT view users (missing users:read) -> 403 Forbidden
    users_resp = await client.get("/v1/users/", headers=headers)
    assert users_resp.status_code == 403

    # 2. Client CANNOT view global workspaces -> 403 Forbidden
    ws_resp = await client.get("/v1/workspaces/", headers=headers)
    assert ws_resp.status_code == 403

    # 3. Client CANNOT register devices -> 403 Forbidden
    dev_resp = await client.post(
        "/v1/devices/",
        headers=headers,
        json={"code": "DEV-CLI-01", "name": "Client Device", "workspace_id": 1},
    )
    assert dev_resp.status_code == 403

    # 4. Client CAN create ticket (tickets:create)
    ticket_resp = await client.post(
        "/v1/tickets/",
        headers=headers,
        json={
            "title": "Broken hydraulic arm",
            "description": "Pressure drop observed during operations",
            "priority": "high",
        },
    )
    assert ticket_resp.status_code == 201
    ticket_data = ticket_resp.json()
    assert ticket_data["title"] == "Broken hydraulic arm"

    # 5. Client CAN list their tickets (tickets:read)
    list_tickets_resp = await client.get("/v1/tickets/", headers=headers)
    assert list_tickets_resp.status_code == 200
    assert len(list_tickets_resp.json()) >= 1


@pytest.mark.asyncio
async def test_me_permissions_endpoint(client):
    # Test Admin permissions
    admin_token = await get_token_for(client, "test@s247.local", "testpass123")
    admin_perms_resp = await client.get(
        "/v1/me/permissions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_perms_resp.status_code == 200
    admin_data = admin_perms_resp.json()
    assert admin_data["role"] == "admin"
    assert Permission.USERS_CREATE.value in admin_data["permissions"]
    assert Permission.WORKSPACES_CREATE.value in admin_data["permissions"]

    # Test Technician permissions
    tech_token = await get_token_for(client, "tech@s247.local", "techpass123")
    tech_perms_resp = await client.get(
        "/v1/me/permissions",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert tech_perms_resp.status_code == 200
    tech_data = tech_perms_resp.json()
    assert tech_data["role"] == "technician"
    assert Permission.USERS_READ.value in tech_data["permissions"]
    assert Permission.DEVICES_CREATE.value in tech_data["permissions"]
    assert Permission.USERS_CREATE.value not in tech_data["permissions"]
    assert Permission.WORKSPACES_CREATE.value not in tech_data["permissions"]

    # Test Client permissions
    client_token = await get_token_for(client, "client@s247.local", "clientpass123")
    cli_perms_resp = await client.get(
        "/v1/me/permissions",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert cli_perms_resp.status_code == 200
    cli_data = cli_perms_resp.json()
    assert cli_data["role"] == "client"
    assert Permission.TICKETS_CREATE.value in cli_data["permissions"]
    assert Permission.USERS_READ.value not in cli_data["permissions"]
    assert Permission.DEVICES_CREATE.value not in cli_data["permissions"]
