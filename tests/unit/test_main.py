"""Unit tests for main orchestration module."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pandas as pd

from main import get_date_range


class TestGetDateRange:
    """Tests for get_date_range function."""

    def test_returns_past_7_days_range(self):
        result = get_date_range()
        start, end = result

        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        expected_start = today - timedelta(days=7)
        expected_end = today - timedelta(days=1)

        assert start.startswith(expected_start.strftime("%Y-%m-%d"))
        assert end.startswith(expected_end.strftime("%Y-%m-%d"))

    def test_excludes_today(self):
        start, end = get_date_range()

        start_dt = datetime.strptime(start[:10], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        end_dt = datetime.strptime(end[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        assert end_dt < today
        assert start_dt < today

    def test_start_date_is_6_days_before_end(self):
        start, end = get_date_range()

        start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.000Z")
        end_dt = datetime.strptime(
            end[:10] + "T00:00:00.000Z", "%Y-%m-%dT%H:%M:%S.000Z"
        )

        difference = (end_dt - start_dt).days
        assert difference == 6

    def test_start_time_is_midnight(self):
        start, _ = get_date_range()
        assert "T00:00:00.000Z" in start

    def test_end_time_is_end_of_day(self):
        _, end = get_date_range()
        assert "T23:59:59.000Z" in end

    def test_returns_iso_format(self):
        start, end = get_date_range()
        assert "T" in start
        assert ".000Z" in start
        assert "T" in end
        assert ".000Z" in end


class TestMainFunction:
    """Tests for the main function orchestration."""

    @patch("src.drive_handler.upload_excel")
    @patch("src.drive_handler.download_csv")
    @patch("src.excel_exporter.export_to_excel")
    @patch("src.doctor_translator.translate_doctor")
    @patch("src.gender_classifier.classify_genders")
    @patch("src.phone_normalizer.normalize_phones")
    @patch("src.appointments.fetch_appointments")
    @patch.dict(
        "os.environ",
        {
            "DRIVE_CSV_FILE_ID": "test-csv-id",
            "DRIVE_EXCEL_FILE_ID": "test-excel-id",
        },
    )
    def test_main_with_empty_appointments(
        self,
        mock_fetch,
        mock_normalize,
        mock_classify,
        mock_translate,
        mock_export,
        mock_download,
        mock_upload,
    ):
        mock_fetch.return_value = pd.DataFrame(
            columns=["Patient", "Date", "Doctor", "PhoneNumber"]
        )

        from main import main

        main()

        mock_fetch.assert_called_once()
        mock_normalize.assert_not_called()
        mock_export.assert_not_called()
        mock_upload.assert_not_called()
