import asyncio
from core.config import settings
import logging
from datetime import datetime

from services.ozon.seller import OzonSellerClient
from services.ozon.performance import OzonPerformanceClient


logging.basicConfig(filemode="a", level=logging.INFO)

since = datetime.strptime("2024-09-01", "%Y-%m-%d").date()
to = datetime.strptime("2024-09-30", "%Y-%m-%d").date()


async def main():
    async with OzonSellerClient(
        client_id=settings.ozon_seller_client_id,
        token=settings.ozon_seller_token,
        timezone=settings.timezone,
    ) as seller_client, OzonPerformanceClient(
        client_id=settings.ozon_performance_client_id,
        token=settings.ozon_performance_token,
        timezone=settings.timezone,
    ) as performence_client:
        # sales = await seller_client.get_posting_fbo_list(since=since, to=to)
        result = await performence_client.get_statistics(since=since, to=to)
        logging.info(f"data: {result}")


asyncio.run(main())
