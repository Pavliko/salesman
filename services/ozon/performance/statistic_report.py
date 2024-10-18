import asyncio
import logging
from datetime import date, datetime, time

import pandas as pd
from sqlalchemy import and_, func, or_, select

from db.session import get_session
from models.ozon import OzonCampaigns
from utils.array import divide_chunks


class OzonPerformanceStatisticsMethodsMixin:
    async def get_campaigns_for_statistics(self, since: date, to: date):
        json = await self.get_daily_report(since, to)
        daily = pd.json_normalize(json["rows"], sep="_")
        return list(daily["id"].unique())

    async def get_campaigns_for_statistics_db(self, since: date, to: date):
        async with get_session() as session:
            stmt = select(OzonCampaigns.campaign_id).where(
                OzonCampaigns.from_date < since,
                or_(
                    OzonCampaigns.state == "CAMPAIGN_STATE_RUNNING",
                    and_(
                        OzonCampaigns.state != "CAMPAIGN_STATE_RUNNING",
                        or_(
                            and_(
                                OzonCampaigns.to_date.isnot(None),
                                OzonCampaigns.to_date > since,
                                OzonCampaigns.to_date < func.now(),
                            ),
                            OzonCampaigns.updated_at > since,
                        ),
                    ),
                ),
                OzonCampaigns.from_date < to,
            )
            result = await session.execute(stmt)
            rows = result.fetchall()
            campaign_ids = [row[0] for row in rows]

        return campaign_ids

    async def statistics_request(self, campaign_ids: int, since: date, to: date):
        if self.session is None:
            raise RuntimeError("Session not started")

        if len(campaign_ids) > self.MAX_CAMPAIGNS:
            raise ValueError(
                f"Переданное количество компаний {len(campaign_ids)} дней, что превышает допустимые {self.MAX_CAMPAIGNS}."
            )
        since_str = (
            datetime.combine(since, time.min).replace(tzinfo=self.zone).isoformat()
        )
        to_str = datetime.combine(to, time.max).replace(tzinfo=self.zone).isoformat()

        json_body = {
            "campaigns": campaign_ids,
            "from": since_str,
            "to": to_str,
            "groupBy": "NO_GROUP_BY",
        }

        retries = 0

        while True:
            if retries > self.MAX_RETRIES:
                raise RuntimeError("Max retries")

            async with self.session.post(
                "/api/client/statistics/json", json=json_body
            ) as r:
                response = await r.json()
                error_value = response.get("error")

                if error_value == "Превышен лимит активных запросов (максимум 1)":
                    await asyncio.sleep(self.STATISTICS_RETRY_TIME)
                    retries += 1
                    continue
                elif error_value:
                    raise Exception(f"Получена ошибка: {error_value}")
                else:
                    uuid = response["UUID"]
                    logging.info(f"Report {uuid} created")
                    await asyncio.sleep(self.STATISTICS_RETRY_TIME)
                    chunk_info = None
                    retries = 0

                    while True:
                        if retries > self.MAX_RETRIES:
                            raise RuntimeError("Max retries")

                        async with self.session.get(
                            f"/api/client/statistics/{uuid}"
                        ) as r:
                            chunk_info = await r.json()

                            state = chunk_info["state"]

                            logging.info(f"Report {uuid} state: {state} ")

                            if state != "NOT_STARTED" and state != "IN_PROGRESS":
                                if state == "OK":
                                    break
                                else:
                                    raise RuntimeError(f"Retort error: {chunk_info}")

                            await asyncio.sleep(self.STATISTICS_RETRY_TIME)
                            retries += 1

                    async with self.session.get(
                        f"/api/client/statistics/report?UUID={uuid}"
                    ) as r:
                        chunk_report_raw = await r.json()

                        chunk_report = []
                        for campaign_id, campaign_data in chunk_report_raw.items():
                            for row in campaign_data["report"]["rows"]:
                                row_data = {"campaign_id": campaign_id}
                                row_data.update(row)
                                chunk_report.append(row_data)

                        chunk_report = pd.DataFrame(chunk_report)

                        logging.info(f"Report loaded and prepared")

                        return chunk_report

    async def get_statistics_report(self, since, to):
        self.validate_dates(since, to)

        logging.info("Performance report load campaigns")
        campaign_ids = await self.get_campaigns_for_statistics(since, to)

        logging.info(
            f"Campaigns loaded. Get statistics for {len(campaign_ids)} campaigns: {campaign_ids}"
        )
        campaign_ids = divide_chunks(campaign_ids, self.MAX_CAMPAIGNS)

        report = None
        i = 1
        for ids in campaign_ids:
            logging.info(f"Process campaigns part {i}: {ids}")
            chunk_report = await self.statistics_request(ids, since, to)
            logging.info(f"Part {i} loaded")
            if report is None:
                report = chunk_report
            else:
                report = pd.concat([report, chunk_report])
            i += 1

        return report

    async def get_daily_report(self, since, to):
        if self.session is None:
            raise RuntimeError("Session not started")

        async with self.session.get(
            f"/api/client/statistics/daily/json?dateFrom={since}&dateTo={to}"
        ) as r:
            return await r.json()
