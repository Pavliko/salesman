import aiohttp
import zoneinfo
import logging
from datetime import date, datetime, time
from yarl import URL


class OzonSellerClient:
    BASE_URL = URL("https://api-seller.ozon.ru/v2")

    def __init__(self, client_id: str, token: str, timezone):
        self.client_id = client_id
        self.token = token
        self.zone = zoneinfo.ZoneInfo(timezone)
        self.session = None

    async def __aenter__(self):
        self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close_session()

    def create_session(self):
        headers = {"Client-Id": self.client_id, "Api-Key": self.token}
        self.session = aiohttp.ClientSession(headers=headers, base_url=self.BASE_URL)

    async def close_session(self):
        await self.session.close()

    async def get_posting_fbo_list(
        self, since: date = date.today(), to: date = date.today()
    ):
        if self.session is None:
            raise RuntimeError("Session not started")

        since_str = (
            datetime.combine(since, time.min).replace(tzinfo=self.zone).isoformat()
        )
        to_str = datetime.combine(to, time.max).replace(tzinfo=self.zone).isoformat()
        url = "/posting/fbo/list"
        limit = 1000
        offset = 0
        all_items = []

        while True:
            json_body = {
                "dir": "ASC",
                "filter": {
                    "since": since_str,
                    "status": "",
                    "to": to_str,
                },
                "limit": limit,
                "offset": offset,
                "translit": True,
                "with": {"analytics_data": True, "financial_data": True},
            }
            logging.info(f"Send request: {json_body}")
            async with self.session.post(url, json=json_body) as r:
                response = await r.json()

            items = response["result"]
            all_items.extend(items)

            if len(items) < limit:
                break

            offset += limit

        return all_items
