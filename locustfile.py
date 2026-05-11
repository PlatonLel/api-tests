from datetime import datetime, timedelta, timezone
from uuid import uuid4

from locust import HttpUser, between, task


class LinkShortenerUser(HttpUser):
    wait_time = between(0.2, 1.0)

    def on_start(self):
        self.created_short_ids = []

    @task(4)
    def create_short_link(self):
        response = self.client.post(
            "/links/shorten",
            json={
                "original_url": f"https://example.com/load/{uuid4()}",
                "expire_at": (
                    datetime.now(timezone.utc) + timedelta(days=30)
                ).isoformat(timespec="minutes"),
            },
            name="POST /links/shorten",
        )
        if response.status_code == 200:
            short_id = response.json().get("short_id")
            if short_id:
                self.created_short_ids.append(short_id)

    @task(1)
    def follow_created_short_link(self):
        if not self.created_short_ids:
            return

        short_id = self.created_short_ids[-1]
        self.client.get(
            f"/links/{short_id}",
            name="GET /links/{short_id}",
            allow_redirects=False,
        )
