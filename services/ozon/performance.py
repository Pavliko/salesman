import aiohttp
import zoneinfo
import logging
import inflection
from datetime import date, datetime, timedelta
from multidict import CIMultiDict
from yarl import URL
import pandas as pd
from db.session import get_session
from models.ozon import OzonCampaigns, OzonCampaignsProducts
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select
import numpy as np


class OzonPerformanceClient:
    BASE_URL = URL("https://api-performance.ozon.ru")
    MAX_DAYS = 62
    MAX_CAMPAIGNS = 10
    CAMPAIGNS_NEEDED_FIELDS = [
        "id",
        "title",
        "state",
        "fromDate",
        "toDate",
        "createdAt",
        "updatedAt",
    ]
    CAMPAIGN_STATUSES = {
        "CAMPAIGN_STATE_RUNNING",
        "CAMPAIGN_STATE_PLANNED",
        "CAMPAIGN_STATE_STOPPED",
        "CAMPAIGN_STATE_INACTIVE",
        "CAMPAIGN_STATE_ARCHIVED",
        "CAMPAIGN_STATE_MODERATION_DRAFT",
        "CAMPAIGN_STATE_MODERATION_IN_PROGRESS",
        "CAMPAIGN_STATE_MODERATION_FAILED",
        "CAMPAIGN_STATE_FINISHED",
    }

    def __init__(self, client_id: str, token: str, timezone):
        self.client_id = client_id
        self.token = token
        self.zone = zoneinfo.ZoneInfo(timezone)
        self.session = None
        self.session_token = None
        self.session_token_type = None
        self.session_token_expired_at = None

    async def __aenter__(self):
        self.create_session()
        await self.refresh_session_token()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close_session()

    def create_session(self):
        self.session = OzonPerformanceClientSession(
            token_manager=self, base_url=self.BASE_URL
        )

    async def close_session(self):
        await self.session.close()

    def _fix_time(self, column):
        return pd.to_datetime(column).dt.tz_localize(None)

    async def upload_campaigns(self):
        campaigns = await self.get_campaigns()

        campaigns = pd.json_normalize(campaigns["list"], sep="_")
        campaigns = campaigns[self.CAMPAIGNS_NEEDED_FIELDS]
        campaigns.columns = [inflection.underscore(col) for col in campaigns.columns]
        campaigns.rename(columns={"id": "campaign_id"}, inplace=True)

        campaigns["campaign_id"] = pd.to_numeric(campaigns["campaign_id"])
        campaigns["created_at"] = self._fix_time(campaigns["created_at"])
        campaigns["updated_at"] = self._fix_time(campaigns["updated_at"])
        campaigns["from_date"] = self._fix_time(campaigns["from_date"])
        campaigns["to_date"] = self._fix_time(campaigns["to_date"])
        campaigns = campaigns.replace({np.nan: None})

        async with get_session() as session:
            # Преобразуем DataFrame в список словарей
            data_to_insert = campaigns.to_dict(orient="records")

            # Создаем запрос на вставку с обновлением
            stmt = pg_insert(OzonCampaigns).values(data_to_insert)
            update_dict = {c.name: c for c in stmt.excluded}

            # Используем ON CONFLICT для обновления в случае совпадения уникального ключа
            stmt = stmt.on_conflict_do_update(
                index_elements=["campaign_id"], set_=update_dict
            )

            await session.execute(stmt)

        return campaigns

    async def upload_campaigns_products(self, state=None):
        async with get_session() as session:
            query = select(OzonCampaigns)
            if state in self.CAMPAIGN_STATUSES:
                query = query.where(OzonCampaigns.state == state)

            result = await session.execute(query)
            campaigns = result.scalars()  # Получаем объекты модели

            # Итерирование по результатам
            values = []
            for campaign in campaigns:
                if campaign.state == "CAMPAIGN_STATE_ARCHIVED":
                    continue
                products = await self.get_campaign_products(campaign.campaign_id)
                logging.info(f"{campaign.campaign_id} products: {products}")
                for product in products["list"]:
                    values.append(
                        {
                            "campaign_id": campaign.campaign_id,
                            "product_id": int(product["id"]),
                        }
                    )

            stmt = (
                pg_insert(OzonCampaignsProducts)
                .values(values)
                .on_conflict_do_nothing(index_elements=["campaign_id", "product_id"])
            )

            await session.execute(stmt)

    async def get_statistics(self, since: date = date.today(), to: date = date.today()):
        # await self.upload_campaigns()
        # await self.upload_campaigns_products(state="CAMPAIGN_STATE_RUNNING")
        await self.upload_campaigns_products()
        # async with get_session() as session:
        #     result = await session.execute(select(OzonCampaigns))
        #     rows = result.scalars().all()

        #     # Преобразование результата в список словарей
        #     data = [row.__dict__ for row in rows]

        #     # Удаляем служебные атрибуты SQLAlchemy (например, '_sa_instance_state')
        #     for item in data:
        #         item.pop("_sa_instance_state", None)

        #     # Преобразуем данные в DataFrame
        #     campaigns = pd.DataFrame(data)

        # return campaigns

    async def get_campaign_products(self, campaign_id):
        if self.session is None:
            raise RuntimeError("Session not started")

        async with self.session.get(f"/api/client/campaign/{campaign_id}/objects") as r:
            return await r.json()

    async def get_campaigns(self):
        if self.session is None:
            raise RuntimeError("Session not started")

        async with self.session.get("/api/client/campaign?advObjectType=SKU") as r:
            return await r.json()

    async def refresh_session_token(self):
        json_body = {
            "client_id": self.client_id,
            "client_secret": self.token,
            "grant_type": "client_credentials",
        }

        async with self.session.post("/api/client/token", json=json_body) as r:
            response = await r.json()
            self.session_token = response["access_token"]
            self.session_token_type = response["token_type"]
            self.session_token_expired_at = datetime.now() + timedelta(
                seconds=response["expires_in"] - 3
            )
            self.session.set_headers(
                {
                    "Authorization": f"{self.session_token_type} {self.session_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )


class OzonPerformanceClientSession(aiohttp.ClientSession):

    def __init__(self, token_manager: OzonPerformanceClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token_manager = token_manager

    async def _request(self, method, url, **kwargs):
        if (
            self._token_manager.session_token_expired_at is not None
            and self._token_manager.session_token_expired_at < datetime.now()
        ):
            await self._token_manager.refresh_token()

        response = await super()._request(method, url, **kwargs)

        if response.status not in (401, 403):
            return response
        else:
            await self._token_manager.refresh_token()
            await response.release()

            return await super()._request(method, url, **kwargs)

    def set_headers(self, headers):
        self._default_headers = CIMultiDict(headers)
