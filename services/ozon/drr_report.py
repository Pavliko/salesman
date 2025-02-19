import asyncio
from datetime import date

import numpy as np
import pandas as pd

from core.config import settings
from services.ozon.performance_client import OzonPerformanceClient
from services.ozon.seller import OzonSellerClient


class OzonDRRReport:
    def __init__(self, since: date, to: date):
        self.since = since
        self.to = to

    async def get_report_dataframe(self):
        async with OzonSellerClient(
            client_id=settings.ozon_seller_client_id,
            token=settings.ozon_seller_token,
            timezone=settings.timezone,
        ) as seller_client, OzonPerformanceClient(
            client_id=settings.ozon_performance_client_id,
            token=settings.ozon_performance_token,
            timezone=settings.timezone,
        ) as performence_client:

            results = await asyncio.gather(
                seller_client.selled_products_statistics(self.since, self.to),
                performence_client.get_statistics(self.since, self.to),
            )

            sales = results[0]
            performance = results[1]

            performance = performance.drop(columns=["price"])
            report = pd.merge(
                sales,
                performance,
                on="sku",
                how="outer",
            )

            del sales
            del performance

            report = await self.fill_missed_data(report, seller_client)

            return report

    async def fill_missed_data(self, report, seller_client):
        sku_without_offer_id = list(report[report["offer_id"].isna()].index)
        if sku_without_offer_id:
            products = await seller_client.get_pruducts_by_sku(sku_without_offer_id)

            products = pd.DataFrame(
                products, columns=["id", "name", "offer_id", "price"]
            )
            products.set_index("id", inplace=True)

            products["price"] = products["price"].astype("float")
            products["offer_id"] = products["offer_id"].astype(int)

            report = report.fillna(products)

            del products

        report["currency_code"] = report["currency_code"].fillna("RUB")
        report = report.fillna(0)

        return report

    def prepare_data(self, report):
        report = report.drop(columns=["name", "currency_code", "campaign_id"])
        report = report.sort_values(by="offer_id")
        report["drr"] = report["moneySpent"] / report["profit"]
        report = report.fillna(0)
        report.replace({"drr": [np.inf, -np.inf]}, 1, inplace=True)
        report = report[
            [
                "offer_id",
                "quantity",
                "price",
                "profit",
                "moneySpent",
                "drr",
                "avgBid",
                "orders",
                "ordersMoney",
                "models",
                "modelsMoney",
            ]
        ]

        return report

    def generate_total(self, report):
        total_profit = report["profit"].sum()
        total_spent = report["moneySpent"].sum()

        return {
            "offer_id": "ИТОГО",
            "quantity": report["quantity"].sum(),
            "price": np.nan,
            "profit": total_profit,
            "moneySpent": total_spent,
            "drr": total_spent / total_profit,
        }

    async def process(self):
        report: pd.DataFrame = await self.get_report_dataframe()
        report = self.prepare_data(report)
        report.loc[""] = self.generate_total(report)

        # report.to_excel(f"report_report_{self.since}_{self.to}.xlsx", index=True)
        # report.to_csv(f"report_report_{self.since}_{self.to}.csv", index=True)
        # report.to_json(f"report_report_{self.since}_{self.to}.json", index=True)

        return report
