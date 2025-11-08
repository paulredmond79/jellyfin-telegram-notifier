"""Integration tests for webhook endpoint."""

import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime, timedelta


@pytest.mark.integration
class TestWebhookMovie:
    """Test webhook endpoint for movie notifications."""

    @patch("app.send_telegram_photo")
    @patch("app.get_youtube_trailer_url")
    @patch("app.mark_item_as_notified")
    def test_movie_webhook_success(self, mock_mark, mock_youtube, mock_telegram, client, sample_movie_payload):
        """Test successful movie notification."""
        mock_youtube.return_value = "https://youtube.com/watch?v=test"
        mock_telegram.return_value = Mock(status_code=200)

        response = client.post("/webhook", data=json.dumps(sample_movie_payload), content_type="application/json")

        assert response.status_code == 200
        assert b"Movie notification was sent to telegram" in response.data
        mock_telegram.assert_called_once()
        mock_mark.assert_called_once_with("Movie", "Test Movie", 2023)

    @patch("app.send_telegram_photo")
    @patch("app.get_youtube_trailer_url")
    @patch("app.item_already_notified")
    def test_movie_webhook_already_notified(
        self, mock_already, mock_youtube, mock_telegram, client, sample_movie_payload
    ):
        """Test movie webhook when already notified."""
        mock_already.return_value = True

        response = client.post("/webhook", data=json.dumps(sample_movie_payload), content_type="application/json")

        assert response.status_code == 200
        mock_telegram.assert_not_called()

    @patch("app.send_telegram_photo")
    @patch("app.get_youtube_trailer_url")
    def test_movie_webhook_notification_message_format(self, mock_youtube, mock_telegram, client, sample_movie_payload):
        """Test that movie notification message is formatted correctly."""
        mock_youtube.return_value = "https://youtube.com/watch?v=trailer"
        mock_telegram.return_value = Mock(status_code=200)

        response = client.post("/webhook", data=json.dumps(sample_movie_payload), content_type="application/json")

        assert response.status_code == 200

        # Check the notification message format
        call_args = mock_telegram.call_args
        message = call_args[0][1]

        assert "*🍿New Movie Added🍿*" in message
        assert "*Test Movie*" in message
        assert "*(2023)*" in message
        assert "A great test movie" in message
        assert "02:00:00" in message
        assert "Trailer" in message
        assert "Watch Now" in message
        assert "http://test-jellyfin.com/web/index.html#!/details?id=movie123" in message

    @patch("app.send_telegram_photo")
    @patch("app.get_youtube_trailer_url")
    def test_movie_webhook_without_year_in_name(self, mock_youtube, mock_telegram, client, sample_movie_payload):
        """Test movie notification handles year in movie name."""
        sample_movie_payload["Name"] = "Test Movie (2023)"
        mock_youtube.return_value = None
        mock_telegram.return_value = Mock(status_code=200)

        response = client.post("/webhook", data=json.dumps(sample_movie_payload), content_type="application/json")

        assert response.status_code == 200

        # Verify year was stripped from movie name
        call_args = mock_telegram.call_args
        message = call_args[0][1]

        # Should have cleaned name in the message
        assert "*Test Movie*" in message
        assert "*(2023)*" in message
        assert "Watch Now" in message


@pytest.mark.integration
class TestWebhookSeason:
    """Test webhook endpoint for season notifications."""

    @patch("app.send_telegram_photo")
    @patch("app.get_item_details")
    @patch("app.mark_item_as_notified")
    def test_season_webhook_success(
        self, mock_mark, mock_get_details, mock_telegram, client, sample_season_payload, mock_jellyfin_item_details
    ):
        """Test successful season notification."""
        mock_get_details.return_value = mock_jellyfin_item_details
        mock_telegram.return_value = Mock(status_code=200)

        response = client.post("/webhook", data=json.dumps(sample_season_payload), content_type="application/json")

        assert response.status_code == 200
        assert b"Season notification was sent to telegram" in response.data
        mock_telegram.assert_called_once()
        mock_mark.assert_called_once_with("Season", "Season 1", 2023)

    @patch("app.send_telegram_photo")
    @patch("app.get_item_details")
    def test_season_webhook_image_fallback(
        self, mock_get_details, mock_telegram, client, sample_season_payload, mock_jellyfin_item_details
    ):
        """Test season notification falls back to series image."""
        mock_get_details.return_value = mock_jellyfin_item_details

        # First call fails (season image), second succeeds (series image)
        mock_telegram.side_effect = [Mock(status_code=404), Mock(status_code=200)]

        response = client.post("/webhook", data=json.dumps(sample_season_payload), content_type="application/json")

        assert response.status_code == 200
        assert mock_telegram.call_count == 2

    @patch("app.send_telegram_photo")
    @patch("app.get_item_details")
    def test_season_webhook_overview_fallback(
        self, mock_get_details, mock_telegram, client, sample_season_payload, mock_jellyfin_item_details
    ):
        """Test season uses series overview if season overview is empty."""
        sample_season_payload["Overview"] = ""
        mock_get_details.return_value = mock_jellyfin_item_details
        mock_telegram.return_value = Mock(status_code=200)

        response = client.post("/webhook", data=json.dumps(sample_season_payload), content_type="application/json")

        assert response.status_code == 200

        # Verify series overview was used
        call_args = mock_telegram.call_args
        message = call_args[0][1]
        assert "Test overview" in message
        assert "Watch Now" in message
        assert "http://test-jellyfin.com/web/index.html#!/details?id=season123" in message


@pytest.mark.integration
class TestWebhookEpisode:
    """Test webhook endpoint for episode notifications."""

    @patch("app.send_telegram_photo")
    @patch("app.get_item_details")
    @patch("app.mark_item_as_notified")
    def test_episode_webhook_success(self, mock_mark, mock_get_details, mock_telegram, client, sample_episode_payload):
        """Test successful episode notification."""
        # Set up mock responses for episode, season, and series details
        episode_details = {
            "Items": [
                {
                    "SeasonId": "season123",
                    "PremiereDate": datetime.now().isoformat(),
                }
            ]
        }
        season_details = {
            "Items": [
                {
                    "SeriesId": "series123",
                    "DateCreated": (datetime.now() - timedelta(days=10)).isoformat(),
                }
            ]
        }

        mock_get_details.side_effect = [episode_details, season_details]
        mock_telegram.return_value = Mock(status_code=200)

        response = client.post("/webhook", data=json.dumps(sample_episode_payload), content_type="application/json")

        assert response.status_code == 200
        assert b"Notification sent to Telegram!" in response.data
        mock_mark.assert_called_once()

        # Verify Watch Now link is in the message
        call_args = mock_telegram.call_args
        message = call_args[0][1]
        assert "Watch Now" in message
        assert "http://test-jellyfin.com/web/index.html#!/details?id=episode123" in message

    @patch("app.send_telegram_photo")
    @patch("app.get_item_details")
    def test_episode_webhook_season_recently_added(
        self, mock_get_details, mock_telegram, client, sample_episode_payload
    ):
        """Test episode notification skipped if season was recently added."""
        episode_details = {
            "Items": [
                {
                    "SeasonId": "season123",
                    "PremiereDate": datetime.now().isoformat(),
                }
            ]
        }
        season_details = {
            "Items": [
                {
                    "SeriesId": "series123",
                    "DateCreated": (datetime.now() - timedelta(days=1)).isoformat(),  # Recently added
                }
            ]
        }

        mock_get_details.side_effect = [episode_details, season_details]

        response = client.post("/webhook", data=json.dumps(sample_episode_payload), content_type="application/json")

        assert response.status_code == 200
        assert b"was added within the last" in response.data
        mock_telegram.assert_not_called()

    @patch("app.send_telegram_photo")
    @patch("app.get_item_details")
    def test_episode_webhook_old_premiere_date(self, mock_get_details, mock_telegram, client, sample_episode_payload):
        """Test episode notification skipped if premiere date is too old."""
        # Old premiere date
        old_date = (datetime.now() - timedelta(days=30)).isoformat()
        sample_episode_payload["PremiereDate"] = old_date

        episode_details = {
            "Items": [
                {
                    "SeasonId": "season123",
                    "PremiereDate": old_date,
                }
            ]
        }
        season_details = {
            "Items": [
                {
                    "SeriesId": "series123",
                    "DateCreated": (datetime.now() - timedelta(days=60)).isoformat(),
                }
            ]
        }

        mock_get_details.side_effect = [episode_details, season_details]

        response = client.post("/webhook", data=json.dumps(sample_episode_payload), content_type="application/json")

        assert response.status_code == 200
        # The response message says "was added more than" instead of "was premiered more than"
        assert b"was added more than" in response.data
        mock_telegram.assert_not_called()

    @patch("app.send_telegram_photo")
    @patch("app.get_item_details")
    def test_episode_webhook_image_fallback(self, mock_get_details, mock_telegram, client, sample_episode_payload):
        """Test episode notification falls back to series image."""
        episode_details = {
            "Items": [
                {
                    "SeasonId": "season123",
                    "PremiereDate": datetime.now().isoformat(),
                }
            ]
        }
        season_details = {
            "Items": [
                {
                    "SeriesId": "series123",
                    "DateCreated": (datetime.now() - timedelta(days=10)).isoformat(),
                }
            ]
        }

        mock_get_details.side_effect = [episode_details, season_details]

        # First call fails (season image), second succeeds (series image)
        mock_telegram.side_effect = [Mock(status_code=404), Mock(status_code=200)]

        response = client.post("/webhook", data=json.dumps(sample_episode_payload), content_type="application/json")

        assert response.status_code == 200
        assert mock_telegram.call_count == 2


@pytest.mark.integration
class TestWebhookErrorHandling:
    """Test webhook endpoint error handling."""

    def test_webhook_unsupported_item_type(self, client):
        """Test webhook with unsupported item type."""
        payload = {
            "ItemType": "UnsupportedType",
            "Name": "Test Item",
            "Year": 2023,
        }

        response = client.post("/webhook", data=json.dumps(payload), content_type="application/json")

        assert response.status_code == 200
        assert b"Item type not supported" in response.data

    def test_webhook_invalid_json(self, client):
        """Test webhook with invalid JSON."""
        response = client.post("/webhook", data="invalid json", content_type="application/json")

        assert response.status_code == 200
        assert b"Error:" in response.data

    @patch("app.send_telegram_photo")
    @patch("app.get_youtube_trailer_url")
    def test_webhook_http_error(self, mock_youtube, mock_telegram, client, sample_movie_payload):
        """Test webhook handles HTTP errors gracefully."""
        from requests.exceptions import HTTPError

        mock_youtube.side_effect = HTTPError("API Error")

        response = client.post("/webhook", data=json.dumps(sample_movie_payload), content_type="application/json")

        assert response.status_code == 200
        # The actual response is the error message itself
        assert b"API Error" in response.data
