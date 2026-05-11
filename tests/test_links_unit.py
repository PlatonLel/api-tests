from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.links.crud import create_link, generate_short_id
from src.links.exceptions import NotUniqueAliasError
from src.links.models import Link
from src.links.schemas import LinkCreate, LinkUpdate


def test_generate_short_id_has_requested_length():
    short_id = generate_short_id(length=10)

    assert len(short_id) == 10


def test_generate_short_id_uses_url_safe_alphabet():
    short_id = generate_short_id(length=50)

    assert short_id.isalnum()


@pytest.mark.anyio
async def test_create_link_rejects_existing_stored_custom_alias(db_session):
    db_session.add(
        Link(
            original_url="https://example.com/first",
            short_id="first",
            custom_alias="repeat",
        )
    )
    await db_session.commit()

    with pytest.raises(NotUniqueAliasError):
        await create_link(
            db=db_session,
            original_url="https://example.com/second",
            custom_alias="repeat",
        )


def test_link_create_rejects_past_expiration_date():
    past_date = datetime.now(timezone.utc) - timedelta(days=1)

    with pytest.raises(ValidationError):
        LinkCreate(original_url="https://example.com", expire_at=past_date)


def test_link_update_rounds_expiration_to_minute():
    expire_at = datetime(2030, 1, 1, 12, 30, 45, 123456, tzinfo=timezone.utc)

    link_update = LinkUpdate(expire_at=expire_at)

    assert link_update.expire_at == datetime(2030, 1, 1, 12, 30, tzinfo=timezone.utc)
