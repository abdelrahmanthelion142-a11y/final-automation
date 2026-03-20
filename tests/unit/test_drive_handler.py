"""Unit tests for Google Drive handler module."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import json

from src.drive_handler import (
    get_service,
    download_csv,
    upload_csv,
    upload_excel,
)


class TestGetService:
    """Tests for get_service function."""

    @patch("src.drive_handler.service_account.Credentials.from_service_account_info")
    @patch("src.drive_handler.build")
    def test_get_service_success(self, mock_build, mock_creds):
        mock_creds.return_value = MagicMock()
        mock_build.return_value = MagicMock()

        with patch.dict(
            "os.environ",
            {"GOOGLE_SERVICE_ACCOUNT_JSON": json.dumps({"type": "service_account"})},
        ):
            result = get_service()

            mock_creds.assert_called_once()
            mock_build.assert_called_once_with(
                "drive", "v3", credentials=mock_creds.return_value
            )

    @patch.dict("os.environ", {}, clear=True)
    def test_get_service_missing_credentials(self):
        with pytest.raises(KeyError):
            get_service()

    @patch("src.drive_handler.service_account.Credentials.from_service_account_info")
    def test_get_service_invalid_json(self, mock_creds):
        mock_creds.side_effect = json.JSONDecodeError("msg", "doc", 0)

        with patch.dict("os.environ", {"GOOGLE_SERVICE_ACCOUNT_JSON": "invalid json"}):
            with pytest.raises(json.JSONDecodeError):
                get_service()


class TestDownloadCsv:
    """Tests for download_csv function."""

    @patch("src.drive_handler.get_service")
    def test_download_csv_success(self, mock_get_service, sample_gender_df):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_request = MagicMock()
        mock_service.files().get_media.return_value = mock_request

        csv_content = "Patient,Gender\nأحمد,Male\nسارة,Female"
        with patch("src.drive_handler.MediaIoBaseDownload") as mock_download:
            mock_downloader = MagicMock()
            mock_download.return_value = mock_downloader
            mock_downloader.next_chunk.return_value = (None, True)

            with patch("pandas.read_csv") as mock_read_csv:
                mock_read_csv.return_value = sample_gender_df

                result = download_csv("test-file-id")

                assert len(result) == 3

    @patch("src.drive_handler.get_service")
    def test_download_csv_api_error(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.files().get_media.side_effect = Exception("API Error")

        result = download_csv("test-file-id")

        assert len(result) == 0
        assert list(result.columns) == ["Patient", "Gender"]

    @patch("src.drive_handler.get_service")
    def test_download_csv_empty_file(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        with patch("src.drive_handler.MediaIoBaseDownload") as mock_download:
            mock_downloader = MagicMock()
            mock_download.return_value = mock_downloader
            mock_downloader.next_chunk.return_value = (None, True)

            with patch("pandas.read_csv") as mock_read_csv:
                mock_read_csv.return_value = pd.DataFrame(columns=["Patient", "Gender"])

                result = download_csv("test-file-id")

                assert len(result) == 0


class TestUploadCsv:
    """Tests for upload_csv function."""

    @patch("src.drive_handler.os.unlink")
    @patch("src.drive_handler.MediaFileUpload")
    @patch("src.drive_handler.get_service")
    @patch("builtins.open", new_callable=mock_open)
    @patch("tempfile.NamedTemporaryFile")
    def test_upload_csv_success(
        self, mock_tempfile, mock_open, mock_get_service, mock_media, mock_unlink
    ):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.csv"
        mock_tempfile.return_value.__enter__ = lambda self: mock_temp
        mock_tempfile.return_value.__exit__ = MagicMock()

        df = pd.DataFrame([{"Patient": "أحمد", "Gender": "Male"}])

        upload_csv(df, "test-file-id")

        mock_service.files().update.assert_called_once()
        mock_unlink.assert_called_once_with("/tmp/test.csv")

    @patch("src.drive_handler.os.unlink")
    @patch("src.drive_handler.MediaFileUpload")
    @patch("src.drive_handler.get_service")
    def test_upload_csv_uses_correct_mime_type(
        self, mock_get_service, mock_media, mock_unlink
    ):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        df = pd.DataFrame([{"Patient": "أحمد", "Gender": "Male"}])

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__ = MagicMock()
            mock_temp.return_value.__exit__ = MagicMock()
            mock_temp.return_value.name = "/tmp/test.csv"

            upload_csv(df, "test-file-id")

            mock_media.assert_called_once()
            call_kwargs = mock_media.call_args[1]
            assert call_kwargs["mimetype"] == "text/csv"


class TestUploadExcel:
    """Tests for upload_excel function."""

    @patch("src.drive_handler.MediaFileUpload")
    @patch("src.drive_handler.get_service")
    def test_upload_excel_success(self, mock_get_service, mock_media):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_media_instance = MagicMock()
        mock_media.return_value = mock_media_instance

        upload_excel("/path/to/file.xlsx", "test-file-id")

        mock_service.files().update.assert_called_once()

    @patch("src.drive_handler.MediaFileUpload")
    @patch("src.drive_handler.get_service")
    def test_upload_excel_uses_correct_mime_type(self, mock_get_service, mock_media):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        upload_excel("/path/to/file.xlsx", "test-file-id")

        mock_media.assert_called_once()
        call_kwargs = mock_media.call_args[1]
        assert "spreadsheetml" in call_kwargs["mimetype"]

    @patch("src.drive_handler.MediaFileUpload")
    @patch("src.drive_handler.get_service")
    def test_upload_excel_includes_resumable(self, mock_get_service, mock_media):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        upload_excel("/path/to/file.xlsx", "test-file-id")

        mock_media.assert_called_once()
        call_kwargs = mock_media.call_args[1]
        assert call_kwargs["resumable"] == True
