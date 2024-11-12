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

since = datetime.strptime("2024-11-11", "%Y-%m-%d").date()
to = datetime.strptime("2024-11-11", "%Y-%m-%d").date()


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

    # df.rename(
    #     columns={
    #         "offer_id": "Артикул",
    #         "quantity": "Заказы в штуках",
    #         "price": "Цена",
    #         "profit": "Стоимость",
    #         "moneySpent": "Расход на рекламу",
    #         "drr": "ДРР%",
    #         "avgBid": "Средняя ставка",
    #         "orders": "Заказы с рекламы",
    #         "ordersMoney": "Стоимость с рекламы",
    #         "models": "Заказы других моделей с рекламы",
    #         "modelsMoney": "Стоимость других моделей с рекламы",
    #     },
    #     inplace=True,
    # )

    # # Замена некорректных значений в DataFrame
    # df = df.fillna("")
    # # Добавление строки с текущей датой для всей вставляемой таблицы
    # if since == to:
    #     current_date = since.strftime("%d.%m.%Y")
    # else:
    #     current_date = f"{since.strftime('%d.%m.%Y')} - {to.strftime('%d.%m.%Y')}"

    # df.insert(0, "Дата", current_date)

    # Настройка доступа к Google Sheets с использованием учетной записи службы
    # SERVICE_ACCOUNT_FILE = "salesman-438218-a812bcd24486.json"
    # SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    # credentials = Credentials.from_service_account_file(
    #     SERVICE_ACCOUNT_FILE, scopes=SCOPES
    # )
    # gc = gspread.authorize(credentials)

    # Извлечение ключа из URL Google Sheets
    # gsheet_url = "https://docs.google.com/spreadsheets/d/1rsCAm-uUqovLlhr3HNS-jsTA0qvDEYSWSaBmP6_LB44/edit"
    # match = re.search(r"/d/([a-zA-Z0-9-_]+)", gsheet_url)
    # if not match:
    #     raise ValueError("Невозможно извлечь ключ из URL Google Sheets")
    # gsheet_key = match.group(1)

    # Открытие Google Sheets по ключу
    # sh = gc.open_by_key(gsheet_key)

    # Проверка, существует ли уже лист с указанным именем
    # months = {
    #     "January": "Январь",
    #     "February": "Февраль",
    #     "March": "Март",
    #     "April": "Апрель",
    #     "May": "Май",
    #     "June": "Июнь",
    #     "July": "Июль",
    #     "August": "Август",
    #     "September": "Сентябрь",
    #     "October": "Октябрь",
    #     "November": "Ноябрь",
    #     "December": "Декабрь",
    # }
    # month_name = datetime.now().strftime("%B")
    # worksheet_name = f"{months[month_name]} {datetime.now().year}"
    # try:
    #     worksheet = sh.worksheet(worksheet_name)
    #     print(f"Лист '{worksheet_name}' уже существует, открываем его.")
    # except gspread.exceptions.WorksheetNotFound:
    #     worksheet = sh.add_worksheet(title=worksheet_name, rows="200", cols="20")
    #     print(f"Создан новый лист с именем '{worksheet_name}'.")

    # Определение позиции следующей свободной клетки в колонке A для вставки данных
    # cell_list = worksheet.col_values(3)
    # next_row = len(cell_list) + 3

    # # Проверка лимита строк и расширение, если необходимо
    # required_rows = next_row + len(df) + 1
    # if required_rows > worksheet.row_count:
    #     worksheet.add_rows(required_rows - worksheet.row_count)

    # # Вставка заголовков и значений из DataFrame в Google Sheets
    # data_headers = [df.columns.values.tolist()]
    # data_values = df.values.tolist()
    # all_data = data_headers + data_values

    # # Вставка всех строк данных за один раз
    # worksheet.append_rows(
    #     all_data, value_input_option="RAW", table_range=f"B{next_row}"
    # )

    # # Форматирование последней вставленной строки
    # last_row_index = next_row + len(all_data) - 1
    # cell_format = CellFormat(
    #     textFormat=TextFormat(
    #         fontSize=14,
    #         foregroundColor=Color(0, 0.69, 0.313),
    #     ),
    # )
    # format_cell_range(
    #     worksheet,
    #     f"C{last_row_index}:C{last_row_index}",
    #     cell_format,
    # )
    # format_cell_range(
    #     worksheet,
    #     f"F{last_row_index}:G{last_row_index}",
    #     cell_format,
    # )

    # worksheet.merge_cells(f"B{next_row + 1}:B{last_row_index}")

    # cell_format = CellFormat(verticalAlignment="MIDDLE")
    # format_cell_range(worksheet, f"B{next_row + 1}", cell_format)

    # # Создаем формат ячеек с черными границами
    # cell_format = CellFormat(
    #     borders=Borders(
    #         top=Border("SOLID", Color(0, 0, 0)),
    #         bottom=Border("SOLID", Color(0, 0, 0)),
    #         left=Border("SOLID", Color(0, 0, 0)),
    #         right=Border("SOLID", Color(0, 0, 0)),
    #     ),
    #     textFormat=TextFormat(bold=True),
    #     horizontalAlignment="CENTER",
    # )

    # # Применяем формат ко всему диапазону вставленных данных
    # format_cell_range(
    #     worksheet,
    #     f"B{next_row}:{chr(65 + len(df.columns))}{last_row_index}",
    #     cell_format,
    # )

    # # Форматирование ячеек по типам данных
    # column_formats = {
    #     "ДРР%": CellFormat(numberFormat={"type": "PERCENT", "pattern": "0.00%"}),
    #     "Расход на рекламу": CellFormat(
    #         numberFormat={"type": "NUMBER", "pattern": "0.00"}
    #     ),
    # }

    # for col_name, col_format in column_formats.items():
    #     if col_name in df.columns:
    #         col_index = (
    #             df.columns.get_loc(col_name) + 1
    #         )  # Получаем индекс колонки (начинается с 0)

    #         format_cell_range(
    #             worksheet,
    #             f"{chr(65 + col_index)}{next_row}:{chr(65 + col_index)}{last_row_index}",
    #             col_format,
    #         )

    # # Скрыть определенные столбцы (например, столбцы B и D)
    # requests = [
    #     {
    #         "updateDimensionProperties": {
    #             "range": {
    #                 "sheetId": worksheet._properties["sheetId"],
    #                 "dimension": "COLUMNS",
    #                 "startIndex": 8,  # Индекс столбца для столбца D
    #                 "endIndex": 13,
    #             },
    #             "properties": {"hiddenByUser": True},
    #             "fields": "hiddenByUser",
    #         }
    #     },
    # ]

    # sh.batch_update({"requests": requests})

    # # Установка ширины для определенных столбцов
    # column_widths = {"C": 300, "D": 125, "G": 145}

    # for col_letter, width in column_widths.items():
    #     set_column_width(worksheet, col_letter, width)

    # print(
    #     f"Данные добавлены в страницу '{worksheet_name}' в Google Sheets по ссылке '{gsheet_url}'."
    # )


asyncio.run(main())
