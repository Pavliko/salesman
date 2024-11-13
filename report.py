import asyncio
import logging
from datetime import datetime

from services.google import GoogleSheetsClient
from services.ozon.drr_report import OzonDRRReport

logging.basicConfig(
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",  # Добавлено время
    datefmt="%Y-%m-%d %H:%M:%S",  # Формат времени
)

since = datetime.strptime("2024-11-12", "%Y-%m-%d").date()
to = datetime.strptime("2024-11-12", "%Y-%m-%d").date()


async def main():
    report = OzonDRRReport(since, to)
    df = await report.process()

    gsheet_client = GoogleSheetsClient(
        "salesman-438218-a812bcd24486.json",
        "https://docs.google.com/spreadsheets/d/1rsCAm-uUqovLlhr3HNS-jsTA0qvDEYSWSaBmP6_LB44/edit",
    )

    gsheet_client.append_drr_report(df, since, to)

    del report

    # # Загрузка DataFrame из CSV файла
    # csv_file_path = f"report_report_{since}_{to}.csv"
    # df = pd.read_csv(csv_file_path)


asyncio.run(main())
