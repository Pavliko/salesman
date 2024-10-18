import aiohttp
import zoneinfo
import logging
from datetime import date, datetime, time, timedelta
import pandas as pd
from yarl import URL


class OzonSellerClient:
    BASE_URL = URL("https://api-seller.ozon.ru/")

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

    async def get_pruducts_by_sku(self, skus):
        if self.session is None:
            raise RuntimeError("Session not started")

        if len(skus) > 1000:
            raise Exception(f"Max skus is 1000. Get {len(skus)}")

        json_body = {"sku": skus}

        async with self.session.post("/v2/product/info/list", json=json_body) as r:
            response = await r.json()

        return response["result"]["items"]

    async def get_posting_fbo_list(self, since: date, to: date):
        if self.session is None:
            raise RuntimeError("Session not started")

        since_str = (
            datetime.combine(since, time.min).replace(tzinfo=self.zone).isoformat()
        )
        to_str = datetime.combine(to, time.max).replace(tzinfo=self.zone).isoformat()
        url = "/v2/posting/fbo/list"
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
                "with": {"analytics_data": False, "financial_data": False},
            }

            async with self.session.post(url, json=json_body) as r:
                response = await r.json()

            items = response["result"]
            all_items.extend(items)

            if len(items) < limit:
                break

            offset += limit

        return all_items

    async def selled_products_statistics(self, since: date, to: date):
        logging.info(f"FBO orders start loading since {since} to {to}")
        orders = await self.get_posting_fbo_list(since, to)

        product_siles = []

        for order in orders:
            if order["status"] == "cancelled":
                continue
            products = order.pop("products")
            for product in products:
                product_siles.append(product)

        products = pd.DataFrame(product_siles)
        products = products.drop(columns=["digital_codes"])
        products["price"] = products["price"].str.replace(",", ".").astype("float")
        products["profit"] = products["quantity"] * products["price"]
        products = products.groupby("sku").agg(
            {
                "name": "first",
                "quantity": "sum",
                "offer_id": "first",
                "price": "max",
                "profit": "sum",
                "currency_code": "first",
            }
        )

        logging.info(f"FBO orders loaded and prepared")

        return products
