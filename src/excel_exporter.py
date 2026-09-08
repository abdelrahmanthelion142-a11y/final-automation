
import urllib.parse
import logging
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font


logger = logging.getLogger(__name__)


def format_date(date_str: str) -> str:
    """Format a date string to remove timezone/time components.

    Args:
        date_str: Date string in various formats (ISO, YYYY-MM-DD, etc.)

    Returns:
        str: Date in YYYY-MM-DD format
    """
    if not date_str or date_str == "nan":
        return ""

    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        else:
            return date_str.split(" ")[0]
    except (ValueError, TypeError):
        return date_str


def make_wa_url(phone: str, message: str) -> str:
    """Generate a WhatsApp click-to-chat URL.

    Args:
        phone: Normalised phone number in local format (starting with 0, e.g., "01012345678")
            or international format (starting with +20 or 20)
        message: The Arabic message to pre-populate

    Returns:
        str: WhatsApp URL (https://wa.me/{phone}?text={encoded_message})
            Returns empty string if phone contains "?" (flagged as invalid by the normalization function)
    """
    if "?" in phone:
        return ""

    clean = phone.replace("+", "").replace(" ", "")

    # add country code 
    if clean.startswith("0"):
        clean = "20" + clean[1:]

    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{clean}?text={encoded_message}" #this link when directly pressed opens a whatsapp chat with the phone number with the message written in the text box all you have to do is press send 


def export_to_excel(df: pd.DataFrame, output_path: str) -> str:
    """Export DataFrame to Excel file with WhatsApp hyperlinks.

    Args:
        df: DataFrame with columns: PhoneNumber, Message, Date
        output_path: Local filesystem path to save the Excel file

    Returns:
        str: The output_path (same as input)

    Side effects:
        - Creates an Excel file at output_path
        - Logs the number of rows written
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Follow-Up"

    ws.append(["PhoneNumber", "Message", "Date", "WhatsApp Link"])

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 80
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 15

    for i, (idx, row) in enumerate(df.iterrows()):
        phone = str(row["PhoneNumber"])
        message = str(row["Message"])
        date = format_date(str(row["Date"]))

        row_num = i + 2
        ws.cell(row=row_num, column=1, value=phone)
        ws.cell(row=row_num, column=2, value=message)
        ws.cell(row=row_num, column=3, value=date)

        if "?" in phone:
            ws.cell(row=row_num, column=4, value="Invalid phone")
        else:
            url = make_wa_url(phone, message)
            ws.cell(row=row_num, column=4, value="Send")
            cell = ws.cell(row=row_num, column=4)
            cell.hyperlink = url
            cell.font = Font(color="0563C1", underline="single")

    wb.save(output_path)
    logger.info(f"Excel written: {output_path} ({len(df)} rows)")

    return output_path
