import logging

import inflection
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from yarl import URL

from db.session import get_session
from models.ozon import OzonCampaigns, OzonCampaignsProducts
import certifi
import ssl


class OzonPerformanceCampaignsMixin:

    def _fix_time(self, column):
        return pd.to_datetime(column).dt.tz_localize(None)

    async def upload_campaigns(self):
        campaigns = await self.get_campaigns()

        campaigns = pd.json_normalize(campaigns["list"])
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

    async def get_campaign_products(self, campaign_id):
        if self.session is None:
            raise RuntimeError("Session not started")

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with self.session.get(f"/api/client/campaign/{campaign_id}/objects", ssl=ssl_context) as r:
            return await r.json()

    async def get_campaigns(self):
        if self.session is None:
            raise RuntimeError("Session not started")

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with self.session.get("/api/client/campaign?advObjectType=SKU", ssl=ssl_context) as r:
            return await r.json()
