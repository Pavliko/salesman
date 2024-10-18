import re
from datetime import date, datetime

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    Border,
    Borders,
    CellFormat,
    Color,
    TextFormat,
    format_cell_range,
    set_column_width,
)


class GoogleSheetsClient:

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    MONTHS = {
        "January": "Январь",
        "February": "Февраль",
        "March": "Март",
        "April": "Апрель",
        "May": "Май",
        "June": "Июнь",
        "July": "Июль",
        "August": "Август",
        "September": "Сентябрь",
        "October": "Октябрь",
        "November": "Ноябрь",
        "December": "Декабрь",
    }

    def __init__(self, service_account_file_path, gsheet_url):
        self.account_file_path = service_account_file_path
        self.gsheet_key = self.extract_gsheet_key(gsheet_url)

    def extract_gsheet_key(self, gsheet_url):
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", gsheet_url)
        if not match:
            raise ValueError("Невозможно извлечь ключ из URL Google Sheets")

        return match.group(1)

    def authorize(self):
        credentials = Credentials.from_service_account_file(
            self.account_file_path, scopes=self.SCOPES
        )
        self.gc = gspread.authorize(credentials)

    def append_drr_report(self, df: pd.DataFrame, since, to):
        self.authorize()

        self.sh = self.gc.open_by_key(self.gsheet_key)
        df = self.prepare_drr_data_frame(df, since, to)

        is_new_worksheet = self.set_worksheet(
            self.extract_mont_name(self.to_datetime(since))
        )
        if is_new_worksheet:
            self.format_drr_worksheet()

        self.insert_report(df)

    def prepare_drr_data_frame(self, df: pd.DataFrame, since, to):
        df.rename(
            columns={
                "offer_id": "Артикул",
                "quantity": "Заказы в штуках",
                "price": "Цена",
                "profit": "Стоимость",
                "moneySpent": "Расход на рекламу",
                "drr": "ДРР%",
                "avgBid": "Средняя ставка",
                "orders": "Заказы с рекламы",
                "ordersMoney": "Стоимость с рекламы",
                "models": "Заказы других моделей с рекламы",
                "modelsMoney": "Стоимость других моделей с рекламы",
            },
            inplace=True,
        )

        # Замена некорректных значений в DataFrame
        df = df.fillna("")
        # Добавление строки с текущей датой для всей вставляемой таблицы
        if since == to:
            current_date = since.strftime("%d.%m.%Y")
        else:
            current_date = f"{since.strftime('%d.%m.%Y')} - {to.strftime('%d.%m.%Y')}"

        df.insert(0, "Дата", current_date)

        return df

    def to_datetime(self, value):
        if isinstance(value, datetime):
            return value
        elif isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        else:
            raise TypeError("Input must be a date or datetime object")

    def extract_mont_name(self, d: datetime):
        month_name = d.strftime("%B")
        return f"{self.MONTHS[month_name]} {d.year}"

    def set_worksheet(self, name):
        try:
            self.worksheet = self.sh.worksheet(name)
            return False
        except gspread.exceptions.WorksheetNotFound:
            self.worksheet = self.sh.add_worksheet(title=name, rows="200", cols="20")
            return True

    def format_drr_worksheet(self):
        # Скрыть определенные столбцы (например, столбцы B и D)
        requests = [
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": self.worksheet._properties["sheetId"],
                        "dimension": "COLUMNS",
                        "startIndex": 8,  # Индекс столбца для столбца D
                        "endIndex": 13,
                    },
                    "properties": {"hiddenByUser": True},
                    "fields": "hiddenByUser",
                }
            },
        ]

        self.sh.batch_update({"requests": requests})

        # Установка ширины для определенных столбцов
        column_widths = {"C": 300, "D": 125, "G": 145}

        for col_letter, width in column_widths.items():
            set_column_width(self.worksheet, col_letter, width)

    def insert_report(self, df: pd.DataFrame):
        cell_list = self.worksheet.col_values(3)
        next_row = len(cell_list) + 3

        # Проверка лимита строк и расширение, если необходимо
        required_rows = next_row + len(df) + 1
        if required_rows > self.worksheet.row_count:
            self.worksheet.add_rows(required_rows - self.worksheet.row_count)

        # Вставка заголовков и значений из DataFrame в Google Sheets
        data_headers = [df.columns.values.tolist()]
        data_values = df.values.tolist()
        all_data = data_headers + data_values

        # Вставка всех строк данных за один раз
        self.worksheet.append_rows(
            all_data, value_input_option="RAW", table_range=f"B{next_row}"
        )

        # Форматирование последней вставленной строки
        last_row_index = next_row + len(all_data) - 1
        cell_format = CellFormat(
            textFormat=TextFormat(
                fontSize=14,
                foregroundColor=Color(0, 0.69, 0.313),
            ),
        )
        format_cell_range(
            self.worksheet,
            f"C{last_row_index}:C{last_row_index}",
            cell_format,
        )
        format_cell_range(
            self.worksheet,
            f"F{last_row_index}:G{last_row_index}",
            cell_format,
        )

        self.worksheet.merge_cells(f"B{next_row + 1}:B{last_row_index}")

        cell_format = CellFormat(verticalAlignment="MIDDLE")
        format_cell_range(self.worksheet, f"B{next_row + 1}", cell_format)

        # Создаем формат ячеек с черными границами
        cell_format = CellFormat(
            borders=Borders(
                top=Border("SOLID", Color(0, 0, 0)),
                bottom=Border("SOLID", Color(0, 0, 0)),
                left=Border("SOLID", Color(0, 0, 0)),
                right=Border("SOLID", Color(0, 0, 0)),
            ),
            textFormat=TextFormat(bold=True),
            horizontalAlignment="CENTER",
        )

        # Применяем формат ко всему диапазону вставленных данных
        format_cell_range(
            self.worksheet,
            f"B{next_row}:{chr(65 + len(df.columns))}{last_row_index}",
            cell_format,
        )

        # Форматирование ячеек по типам данных
        column_formats = {
            "ДРР%": CellFormat(numberFormat={"type": "PERCENT", "pattern": "0.00%"}),
            "Расход на рекламу": CellFormat(
                numberFormat={"type": "NUMBER", "pattern": "0.00"}
            ),
        }

        for col_name, col_format in column_formats.items():
            if col_name in df.columns:
                col_index = (
                    df.columns.get_loc(col_name) + 1
                )  # Получаем индекс колонки (начинается с 0)

                format_cell_range(
                    self.worksheet,
                    f"{chr(65 + col_index)}{next_row}:{chr(65 + col_index)}{last_row_index}",
                    col_format,
                )
