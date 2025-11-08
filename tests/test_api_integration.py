"""Unit tests for API integration functions."""

import pytest
from unittest.mock import patch, Mock
from requests.exceptions import HTTPError, RequestException, Timeout
import app


@pytest.mark.unit
class TestJellyfinAPI:
    """Test Jellyfin API integration functions."""

    @patch("app.http_session.get")
    def test_get_item_details_success(self, mock_get, mock_jellyfin_item_details):
        """Test successful item details retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_jellyfin_item_details
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = app.get_item_details("item123")

        assert result == mock_jellyfin_item_details
        mock_get.assert_called_once()

        # Verify URL construction
        call_args = mock_get.call_args
        assert "item123" in call_args[0][0]

    @patch("app.http_session.get")
    def test_get_item_details_http_error(self, mock_get):
        """Test get_item_details handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("API Error")
        mock_get.return_value = mock_response

        with pytest.raises(HTTPError):
            app.get_item_details("item123")

    @patch("app.http_session.get")
    def test_get_item_details_api_key_in_params(self, mock_get):
        """Test that API key is included in request parameters."""
        mock_response = Mock()
        mock_response.json.return_value = {"Items": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        app.get_item_details("item123")

        # Check that api_key was passed in params
        call_args = mock_get.call_args
        assert "params" in call_args[1]
        assert "api_key" in call_args[1]["params"]


@pytest.mark.unit
class TestYouTubeAPI:
    """Test YouTube API integration functions."""

    @patch("app.http_session.get")
    def test_get_youtube_trailer_url_success(self, mock_get, mock_youtube_response):
        """Test successful YouTube trailer URL retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_youtube_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = app.get_youtube_trailer_url("Test Movie Trailer 2023")

        assert result == "https://www.youtube.com/watch?v=test_video_id"
        mock_get.assert_called_once()

    @patch("app.http_session.get")
    def test_get_youtube_trailer_url_no_results(self, mock_get):
        """Test YouTube API with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = app.get_youtube_trailer_url("Nonexistent Movie")

        assert result == "Video not found!"

    @patch("app.http_session.get")
    def test_get_youtube_trailer_url_http_error(self, mock_get):
        """Test YouTube API handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("API Error")
        mock_get.return_value = mock_response

        with pytest.raises(HTTPError):
            app.get_youtube_trailer_url("Test Movie")

    @patch("app.YOUTUBE_API_KEY", None)
    def test_get_youtube_trailer_url_no_api_key(self):
        """Test YouTube API returns None when no API key is set."""
        result = app.get_youtube_trailer_url("Test Movie")

        assert result is None

    @patch("app.http_session.get")
    def test_get_youtube_trailer_url_malformed_response(self, mock_get):
        """Test YouTube API handles malformed response."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": [{"id": {}}]}  # Missing videoId
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = app.get_youtube_trailer_url("Test Movie")

        assert result == "Video not found!"


@pytest.mark.unit
class TestTelegramAPI:
    """Test Telegram API integration functions."""

    @patch("app.http_session.post")
    @patch("app.http_session.get")
    def test_send_telegram_photo_success(self, mock_get, mock_post, mock_image_response, mock_telegram_response):
        """Test successful Telegram photo sending."""
        mock_get.return_value = mock_image_response
        mock_image_response.raise_for_status = Mock()
        mock_post.return_value = mock_telegram_response

        result = app.send_telegram_photo("photo123", "Test caption")

        assert result.status_code == 200
        mock_get.assert_called_once()
        mock_post.assert_called_once()

        # Verify the post call includes proper data
        call_args = mock_post.call_args
        assert "data" in call_args[1]
        assert call_args[1]["data"]["caption"] == "Test caption"
        assert call_args[1]["data"]["parse_mode"] == "Markdown"

    @patch("app.http_session.post")
    @patch("app.http_session.get")
    def test_send_telegram_photo_image_download(self, mock_get, mock_post, mock_image_response, mock_telegram_response):
        """Test that image is downloaded from Jellyfin."""
        mock_get.return_value = mock_image_response
        mock_image_response.raise_for_status = Mock()
        mock_post.return_value = mock_telegram_response

        app.send_telegram_photo("photo123", "Test caption")

        # Verify image was downloaded from Jellyfin
        call_args = mock_get.call_args
        assert "photo123" in call_args[0][0]
        assert "Images/Primary" in call_args[0][0]

    @patch("app.http_session.post")
    @patch("app.http_session.get")
    def test_send_telegram_photo_with_markdown(self, mock_get, mock_post, mock_image_response, mock_telegram_response):
        """Test that Markdown formatting is preserved."""
        mock_get.return_value = mock_image_response
        mock_image_response.raise_for_status = Mock()
        mock_post.return_value = mock_telegram_response

        caption_with_markdown = "*Bold* _Italic_ [Link](http://example.com)"
        app.send_telegram_photo("photo123", caption_with_markdown)

        call_args = mock_post.call_args
        assert call_args[1]["data"]["caption"] == caption_with_markdown
        assert call_args[1]["data"]["parse_mode"] == "Markdown"


@pytest.mark.unit
class TestHTTPRequestEnhancements:
    """Test timeout, retry, and error handling enhancements."""

    @patch("app.http_session.get")
    def test_get_item_details_includes_timeout(self, mock_get):
        """Test that get_item_details includes timeout parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {"Items": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        app.get_item_details("item123")

        # Verify timeout was passed
        call_args = mock_get.call_args
        assert "timeout" in call_args[1]
        assert call_args[1]["timeout"] == app.REQUEST_TIMEOUT

    @patch("app.http_session.get")
    def test_youtube_api_includes_timeout(self, mock_get):
        """Test that get_youtube_trailer_url includes timeout parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        app.get_youtube_trailer_url("Test Movie")

        # Verify timeout was passed
        call_args = mock_get.call_args
        assert "timeout" in call_args[1]
        assert call_args[1]["timeout"] == app.REQUEST_TIMEOUT

    @patch("app.http_session.post")
    @patch("app.http_session.get")
    def test_send_telegram_photo_includes_timeouts(
        self, mock_get, mock_post, mock_image_response, mock_telegram_response
    ):
        """Test that send_telegram_photo includes timeout parameters."""
        mock_get.return_value = mock_image_response
        mock_image_response.raise_for_status = Mock()
        mock_post.return_value = mock_telegram_response

        app.send_telegram_photo("photo123", "Test caption")

        # Verify image download timeout
        get_call_args = mock_get.call_args
        assert "timeout" in get_call_args[1]
        assert get_call_args[1]["timeout"] == app.IMAGE_DOWNLOAD_TIMEOUT

        # Verify telegram post timeout
        post_call_args = mock_post.call_args
        assert "timeout" in post_call_args[1]
        assert post_call_args[1]["timeout"] == app.REQUEST_TIMEOUT

    @patch("app.http_session.get")
    def test_send_telegram_photo_handles_image_download_failure(self, mock_get):
        """Test that send_telegram_photo raises exception on image download failure."""
        mock_get.side_effect = RequestException("Connection failed")

        with pytest.raises(RequestException):
            app.send_telegram_photo("photo123", "Test caption")

    @patch("app.http_session.get")
    def test_send_telegram_photo_handles_timeout(self, mock_get):
        """Test that send_telegram_photo raises exception on timeout."""
        mock_get.side_effect = Timeout("Request timed out")

        with pytest.raises(Timeout):
            app.send_telegram_photo("photo123", "Test caption")

    @patch("app.http_session.get")
    def test_send_telegram_photo_handles_http_error(self, mock_get):
        """Test that send_telegram_photo raises exception on HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(HTTPError):
            app.send_telegram_photo("photo123", "Test caption")

    def test_session_has_retry_configuration(self):
        """Test that http_session is configured with retry logic."""
        # Verify the session exists and has adapters configured
        assert hasattr(app, "http_session")
        assert "http://" in app.http_session.adapters
        assert "https://" in app.http_session.adapters

        # Check that the adapter has a Retry configuration
        http_adapter = app.http_session.adapters["http://"]
        https_adapter = app.http_session.adapters["https://"]

        assert http_adapter.max_retries.total == app.MAX_RETRIES
        assert https_adapter.max_retries.total == app.MAX_RETRIES

    def test_retry_constants_defined(self):
        """Test that retry constants are properly defined."""
        assert hasattr(app, "REQUEST_TIMEOUT")
        assert hasattr(app, "IMAGE_DOWNLOAD_TIMEOUT")
        assert hasattr(app, "MAX_RETRIES")
        assert hasattr(app, "RETRY_BACKOFF_FACTOR")

        assert app.REQUEST_TIMEOUT == 30
        assert app.IMAGE_DOWNLOAD_TIMEOUT == 60
        assert app.MAX_RETRIES == 3
        assert app.RETRY_BACKOFF_FACTOR == 1
