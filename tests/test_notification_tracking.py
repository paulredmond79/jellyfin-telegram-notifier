"""Unit tests for notification tracking functions."""

import pytest
import json
from unittest.mock import patch
import app


@pytest.mark.unit
class TestNotificationTracking:
    """Test notification tracking functions."""

    def test_load_notified_items_existing_file(self, temp_data_file):
        """Test loading notified items from existing file."""
        # Write test data
        test_data = {"Movie:Test:2023": True}
        with open(temp_data_file, "w") as f:
            json.dump(test_data, f)

        # Mock the file path
        with patch("app.notified_items_file", temp_data_file):
            result = app.load_notified_items()
            assert result == test_data

    def test_load_notified_items_nonexistent_file(self):
        """Test loading notified items when file doesn't exist."""
        with patch("app.notified_items_file", "/nonexistent/path/file.json"):
            result = app.load_notified_items()
            assert result == {}

    def test_save_notified_items(self, temp_data_file):
        """Test saving notified items to file."""
        test_data = {"Movie:Test Movie:2023": True, "Season:Season 1:2023": True}

        with patch("app.notified_items_file", temp_data_file):
            app.save_notified_items(test_data)

            # Verify file contents
            with open(temp_data_file, "r") as f:
                saved_data = json.load(f)

            assert saved_data == test_data

    def test_item_already_notified_true(self):
        """Test item_already_notified when item exists."""
        with patch("app.notified_items", {"Movie:Test Movie:2023": True}):
            result = app.item_already_notified("Movie", "Test Movie", 2023)
            assert result is True

    def test_item_already_notified_false(self):
        """Test item_already_notified when item doesn't exist."""
        with patch("app.notified_items", {}):
            result = app.item_already_notified("Movie", "Test Movie", 2023)
            assert result is False

    def test_mark_item_as_notified(self, temp_data_file):
        """Test marking an item as notified."""
        with patch("app.notified_items_file", temp_data_file):
            with patch("app.notified_items", {}):
                app.mark_item_as_notified("Movie", "Test Movie", 2023)

                # Check the item was added
                key = "Movie:Test Movie:2023"
                assert key in app.notified_items
                assert app.notified_items[key] is True

    def test_mark_item_as_notified_max_entries(self, temp_data_file):
        """Test that old entries are removed when max is exceeded."""
        # Create initial data with max entries
        initial_data = {f"Movie:Movie{i}:2023": True for i in range(100)}

        with patch("app.notified_items_file", temp_data_file):
            with patch("app.notified_items", initial_data):
                # Add one more item
                app.mark_item_as_notified("Movie", "New Movie", 2023)

                # Should have exactly 100 items (oldest one removed)
                assert len(app.notified_items) == 100
                assert "Movie:New Movie:2023" in app.notified_items

    def test_mark_item_as_notified_custom_max(self, temp_data_file):
        """Test mark_item_as_notified with custom max_entries."""
        initial_data = {f"Movie:Movie{i}:2023": True for i in range(10)}

        with patch("app.notified_items_file", temp_data_file):
            with patch("app.notified_items", initial_data):
                # Add with max_entries=10
                app.mark_item_as_notified("Movie", "New Movie", 2023, max_entries=10)

                # Should have exactly 10 items
                assert len(app.notified_items) == 10
                assert "Movie:New Movie:2023" in app.notified_items

    def test_notified_items_key_format(self):
        """Test the key format for notified items."""
        with patch("app.notified_items", {}):
            key = "Movie:The Matrix:1999"
            app.notified_items[key] = True

            assert app.item_already_notified("Movie", "The Matrix", 1999) is True
            assert app.item_already_notified("Movie", "The Matrix", 2000) is False
            assert app.item_already_notified("Season", "The Matrix", 1999) is False
