"""Test configuration and fixtures."""
import os
import json
import pytest
import tempfile
from unittest.mock import Mock, patch
from datetime import datetime

# Set environment variables before importing app module
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_bot_token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "test_chat_id")
os.environ.setdefault("JELLYFIN_BASE_URL", "http://test-jellyfin.com")
os.environ.setdefault("JELLYFIN_API_KEY", "test_api_key")
os.environ.setdefault("YOUTUBE_API_KEY", "test_youtube_key")
os.environ.setdefault("EPISODE_PREMIERED_WITHIN_X_DAYS", "7")
os.environ.setdefault("SEASON_ADDED_WITHIN_X_DAYS", "3")


@pytest.fixture
def test_env_vars():
    """Set up test environment variables."""
    env_vars = {
        "TELEGRAM_BOT_TOKEN": "test_bot_token",
        "TELEGRAM_CHAT_ID": "test_chat_id",
        "JELLYFIN_BASE_URL": "http://test-jellyfin.com",
        "JELLYFIN_API_KEY": "test_api_key",
        "YOUTUBE_API_KEY": "test_youtube_key",
        "EPISODE_PREMIERED_WITHIN_X_DAYS": "7",
        "SEASON_ADDED_WITHIN_X_DAYS": "3",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def temp_data_file():
    """Create a temporary file for notified items."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
        json.dump({}, f)

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    # Cleanup is handled by pytest's tmpdir
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_notified_items():
    """Sample notified items data."""
    return {
        "Movie:Test Movie:2023": True,
        "Season:Season 1:2023": True,
        "Episode:Test Episode:2023": True,
    }


@pytest.fixture
def sample_movie_payload():
    """Sample movie webhook payload from Jellyfin."""
    return {
        "ItemType": "Movie",
        "Name": "Test Movie",
        "Year": 2023,
        "ItemId": "movie123",
        "Overview": "A great test movie",
        "RunTime": "02:00:00",
    }


@pytest.fixture
def sample_season_payload():
    """Sample season webhook payload from Jellyfin."""
    return {
        "ItemType": "Season",
        "Name": "Season 1",
        "Year": 2023,
        "ItemId": "season123",
        "SeriesName": "Test Series",
        "Overview": "First season",
    }


@pytest.fixture
def sample_episode_payload():
    """Sample episode webhook payload from Jellyfin."""
    today = datetime.now().isoformat()
    return {
        "ItemType": "Episode",
        "Name": "Test Episode",
        "Year": 2023,
        "ItemId": "episode123",
        "SeriesName": "Test Series",
        "EpisodeNumber00": "01",
        "SeasonNumber00": "01",
        "Overview": "A test episode",
        "PremiereDate": today,
    }


@pytest.fixture
def mock_jellyfin_item_details():
    """Mock Jellyfin API item details response."""
    return {
        "Items": [
            {
                "Id": "item123",
                "SeriesId": "series123",
                "SeasonId": "season123",
                "DateCreated": "2023-01-01T00:00:00.0000000Z",
                "PremiereDate": "2023-01-01T00:00:00.0000000Z",
                "Overview": "Test overview",
            }
        ]
    }


@pytest.fixture
def mock_youtube_response():
    """Mock YouTube API search response."""
    return {"items": [{"id": {"videoId": "test_video_id"}, "snippet": {"title": "Test Trailer"}}]}


@pytest.fixture
def mock_telegram_response():
    """Mock Telegram API response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True}
    return mock_response


@pytest.fixture
def mock_image_response():
    """Mock image download response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"fake_image_data"
    return mock_response


@pytest.fixture
def flask_app(test_env_vars, temp_data_file, temp_log_dir, monkeypatch):
    """Create a Flask app instance for testing."""
    # Patch file paths before importing app
    monkeypatch.setattr("app.notified_items_file", temp_data_file)
    monkeypatch.setattr("app.log_directory", temp_log_dir)

    # Import after patching environment
    import app as app_module

    # Reload the module to pick up the test environment
    import importlib

    importlib.reload(app_module)

    app_module.app.config["TESTING"] = True

    yield app_module.app

    # Reset notified_items
    app_module.notified_items = {}


@pytest.fixture
def client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()
