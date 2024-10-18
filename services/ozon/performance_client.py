import logging
import zoneinfo
from datetime import date, datetime, time, timedelta

import aiohttp
import inflection
import numpy as np
import pandas as pd
from multidict import CIMultiDict
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from yarl import URL

from db.session import get_session
from models.ozon import OzonCampaigns, OzonCampaignsProducts
from services.ozon.performance.campaigns import OzonPerformanceCampaignsMixin
from services.ozon.performance.client_session import OzonPerformanceClientSession
from services.ozon.performance.statistic_report import (
    OzonPerformanceStatisticsMethodsMixin,
)


class OzonPerformanceClient(
    OzonPerformanceCampaignsMixin, OzonPerformanceStatisticsMethodsMixin
):
    BASE_URL = URL("https://api-performance.ozon.ru")
    MAX_DAYS = 62
    MAX_CAMPAIGNS = 10
    STATISTICS_RETRY_TIME = 20
    MAX_RETRIES = 60
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

    def validate_dates(self, since: date, to: date):
        delta = abs(since - to)
        if delta.days > self.MAX_DAYS:
            raise ValueError(
                f"Разница между датами составляет {delta.days} дней, что превышает допустимые {self.MAX_DAYS} дней."
            )

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

    async def get_statistics(self, since: date, to: date):
        self.validate_dates(since, to)

        logging.info(f"Performance statistics start loading since {since} to {to}")

        report = await self.get_statistics_report(since, to)

        # report.to_excel("data.xlsx", index=False)
        # report = pd.read_excel("data.xlsx")

        # report.to_parquet("data.parquet")
        # report = pd.read_parquet("data.parquet")

        report_columns = {
            "sku": "int",
            "views": "int",
            "clicks": "int",
            "moneySpent": "float",
            "avgBid": "float",
            "orders": "int",
            "ordersMoney": "float",
            "models": "int",
            "modelsMoney": "float",
            "price": "float",
        }

        report = report.drop(columns=["ctr", "title"])

        for name in report_columns:
            if report_columns[name] == "float":
                report[name] = report[name].str.replace(",", ".")

        report = report.astype(report_columns)
        report = report.groupby("sku").agg(
            {
                "views": "sum",
                "clicks": "sum",
                "moneySpent": "sum",
                "avgBid": "mean",
                "orders": "sum",
                "ordersMoney": "sum",
                "models": "sum",
                "modelsMoney": "sum",
                "campaign_id": lambda x: ", ".join(map(str, x)),
                "price": "mean",
            }
        )

        logging.info("Performance statistics loaded and prepared")

        return report
