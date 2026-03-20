"""Excel exporter module for generating follow-up Excel files.

This module creates Excel files with WhatsApp hyperlinks for each
patient follow-up message.
"""

import urllib.parse
import logging

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment


logger = logging.getLogger(__name__)


def make_wa_url(phone: str, message: str) -> str:
    """Generate a WhatsApp click-to-chat URL.

    Args:
        phone: Normalised phone number in local format (starting with 0, e.g., "01012345678")
            or international format (starting with +20 or 20)
        message: The Arabic message to pre-populate

    Returns:
        str: WhatsApp URL (https://wa.me/{phone}?text={encoded_message})
            Returns empty string if phone contains "?" (flagged as invalid)
    """
    if "?" in phone:
        return ""

    clean = phone.replace("+", "").replace(" ", "")

    # Convert local format (starting with 0) to international format
    if clean.startswith("0"):
        clean = "20" + clean[1:]

    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{clean}?text={encoded_message}"


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

    # Make the columns wider for readability
    ws.column_dimensions['A'].width = 18  # PhoneNumber
    ws.column_dimensions['B'].width = 65  # Message
    ws.column_dimensions['C'].width = 25  # Date
    ws.column_dimensions['D'].width = 18  # WhatsApp Link

    ws.append(["PhoneNumber", "Message", "Date", "WhatsApp Link"])

    for i, (idx, row) in enumerate(df.iterrows()):
        phone = str(row["PhoneNumber"])
        message = str(row["Message"])
        date = str(row["Date"])

        row_num = i + 2
        ws.cell(row=row_num, column=1, value=phone)
        
        msg_cell = ws.cell(row=row_num, column=2, value=message)
        msg_cell.alignment = Alignment(wrap_text=True)  # Allow multi-line messages
        
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
