"""Unit tests for API integration functions."""
import pytest
from unittest.mock import patch, Mock
from requests.exceptions import HTTPError
import app


@pytest.mark.unit
class TestJellyfinAPI:
    """Test Jellyfin API integration functions."""

    @patch("app.requests.get")
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

    @patch("app.requests.get")
    def test_get_item_details_http_error(self, mock_get):
        """Test get_item_details handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("API Error")
        mock_get.return_value = mock_response

        with pytest.raises(HTTPError):
            app.get_item_details("item123")

    @patch("app.requests.get")
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

    @patch("app.requests.get")
    def test_get_youtube_trailer_url_success(self, mock_get, mock_youtube_response):
        """Test successful YouTube trailer URL retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_youtube_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = app.get_youtube_trailer_url("Test Movie Trailer 2023")

        assert result == "https://www.youtube.com/watch?v=test_video_id"
        mock_get.assert_called_once()

    @patch("app.requests.get")
    def test_get_youtube_trailer_url_no_results(self, mock_get):
        """Test YouTube API with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = app.get_youtube_trailer_url("Nonexistent Movie")

        assert result == "Video not found!"

    @patch("app.requests.get")
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

    @patch("app.requests.get")
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

    @patch("app.requests.post")
    @patch("app.requests.get")
    def test_send_telegram_photo_success(self, mock_get, mock_post, mock_image_response, mock_telegram_response):
        """Test successful Telegram photo sending."""
        mock_get.return_value = mock_image_response
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

    @patch("app.requests.post")
    @patch("app.requests.get")
    def test_send_telegram_photo_image_download(self, mock_get, mock_post, mock_image_response, mock_telegram_response):
        """Test that image is downloaded from Jellyfin."""
        mock_get.return_value = mock_image_response
        mock_post.return_value = mock_telegram_response

        app.send_telegram_photo("photo123", "Test caption")

        # Verify image was downloaded from Jellyfin
        call_args = mock_get.call_args
        assert "photo123" in call_args[0][0]
        assert "Images/Primary" in call_args[0][0]

    @patch("app.requests.post")
    @patch("app.requests.get")
    def test_send_telegram_photo_with_markdown(self, mock_get, mock_post, mock_image_response, mock_telegram_response):
        """Test that Markdown formatting is preserved."""
        mock_get.return_value = mock_image_response
        mock_post.return_value = mock_telegram_response

        caption_with_markdown = "*Bold* _Italic_ [Link](http://example.com)"
        app.send_telegram_photo("photo123", caption_with_markdown)

        call_args = mock_post.call_args
        assert call_args[1]["data"]["caption"] == caption_with_markdown
        assert call_args[1]["data"]["parse_mode"] == "Markdown"
