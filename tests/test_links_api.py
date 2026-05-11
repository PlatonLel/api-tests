import pytest


@pytest.mark.anyio
async def test_create_short_link_without_user(client):
    response = await client.post(
        "/links/shorten",
        json={"original_url": "https://example.com", "expire_at": None},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://example.com/"
    assert len(data["short_id"]) == 6


@pytest.mark.anyio
async def test_redirect_increments_click_count(client, mock_optional_owner, mock_required_owner):
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/article",
            "custom_alias": "article",
            "expire_at": None,
        },
    )
    short_id = create_response.json()["short_id"]

    redirect_response = await client.get(f"/links/{short_id}")
    stats_response = await client.get(f"/links/{short_id}/stats")

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://example.com/article"
    assert stats_response.status_code == 200
    assert stats_response.json()["click_count"] == 1


@pytest.mark.anyio
async def test_stats_are_hidden_from_another_user(client, mock_optional_owner, mock_required_other):
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/private",
            "custom_alias": "private",
            "expire_at": None,
        },
    )
    short_id = create_response.json()["short_id"]

    response = await client.get(f"/links/{short_id}/stats")

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


@pytest.mark.anyio
async def test_update_link_as_owner(client, mock_optional_owner, mock_required_owner):
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/old",
            "custom_alias": "update",
            "expire_at": None,
        },
    )
    short_id = create_response.json()["short_id"]

    response = await client.put(
        f"/links/{short_id}",
        json={"original_url": "https://example.com/new"},
    )

    assert response.status_code == 200
    assert response.json()["original_url"] == "https://example.com/new"


@pytest.mark.anyio
async def test_update_missing_link_returns_404(client, mock_required_owner):
    response = await client.put(
        "/links/missing",
        json={"original_url": "https://example.com/new"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


@pytest.mark.anyio
async def test_update_link_from_another_user_returns_404(client, mock_optional_owner, mock_required_other):
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/owned",
            "custom_alias": "owned",
            "expire_at": None,
        },
    )
    short_id = create_response.json()["short_id"]

    response = await client.put(
        f"/links/{short_id}",
        json={"original_url": "https://example.com/stolen"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


@pytest.mark.anyio
async def test_delete_link_as_owner_then_read_returns_404(client, mock_optional_owner, mock_required_owner):
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/delete",
            "custom_alias": "delete",
            "expire_at": None,
        },
    )
    short_id = create_response.json()["short_id"]

    delete_response = await client.delete(f"/links/{short_id}")
    read_response = await client.get(f"/links/{short_id}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "success"}
    assert read_response.status_code == 404


@pytest.mark.anyio
async def test_delete_missing_link_returns_404(client, mock_required_owner):
    response = await client.delete("/links/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


@pytest.mark.anyio
async def test_delete_link_from_another_user_returns_404(client, mock_optional_owner, mock_required_other):
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/owned-delete",
            "custom_alias": "owneddel",
            "expire_at": None,
        },
    )
    short_id = create_response.json()["short_id"]

    response = await client.delete(f"/links/{short_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


@pytest.mark.anyio
async def test_unknown_short_link_returns_404(client):
    response = await client.get("/links/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


@pytest.mark.anyio
async def test_invalid_url_is_rejected(client):
    response = await client.post(
        "/links/shorten",
        json={"original_url": "not a url", "expire_at": None},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_custom_alias_can_use_boundary_lengths(client):
    min_alias_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/min",
            "custom_alias": "abcd",
            "expire_at": None,
        },
    )
    max_alias_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/max",
            "custom_alias": "a" * 16,
            "expire_at": None,
        },
    )

    assert min_alias_response.status_code == 200
    assert min_alias_response.json()["short_id"] == "abcd"
    assert max_alias_response.status_code == 200
    assert max_alias_response.json()["short_id"] == "a" * 16


@pytest.mark.anyio
async def test_custom_alias_rejects_invalid_characters(client):
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/bad-alias",
            "custom_alias": "bad alias",
            "expire_at": None,
        },
    )

    assert response.status_code == 422
