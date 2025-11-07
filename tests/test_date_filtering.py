"""Unit tests for date filtering functions."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import app


@pytest.mark.unit
class TestDateFiltering:
    """Test date filtering functions."""

    def test_is_within_last_x_days_recent_date(self):
        """Test is_within_last_x_days with a recent date."""
        # Date from 3 days ago
        recent_date = (datetime.now() - timedelta(days=3)).isoformat()
        assert app.is_within_last_x_days(recent_date, 7) is True

    def test_is_within_last_x_days_old_date(self):
        """Test is_within_last_x_days with an old date."""
        # Date from 10 days ago
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        assert app.is_within_last_x_days(old_date, 7) is False

    def test_is_within_last_x_days_exact_boundary(self):
        """Test is_within_last_x_days at exact boundary."""
        # Date from exactly 7 days ago
        boundary_date = (datetime.now() - timedelta(days=7)).isoformat()
        assert app.is_within_last_x_days(boundary_date, 7) is False

    def test_is_within_last_x_days_today(self):
        """Test is_within_last_x_days with today's date."""
        today = datetime.now().isoformat()
        assert app.is_within_last_x_days(today, 7) is True

    def test_is_not_within_last_x_days_recent_date(self):
        """Test is_not_within_last_x_days with a recent date."""
        # Date from 1 day ago
        recent_date = (datetime.now() - timedelta(days=1)).isoformat()
        assert app.is_not_within_last_x_days(recent_date, 3) is False

    def test_is_not_within_last_x_days_old_date(self):
        """Test is_not_within_last_x_days with an old date."""
        # Date from 10 days ago
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        assert app.is_not_within_last_x_days(old_date, 3) is True

    def test_is_not_within_last_x_days_exact_boundary(self):
        """Test is_not_within_last_x_days at exact boundary."""
        # Date from exactly 3 days ago
        boundary_date = (datetime.now() - timedelta(days=3)).isoformat()
        assert app.is_not_within_last_x_days(boundary_date, 3) is True

    def test_is_not_within_last_x_days_today(self):
        """Test is_not_within_last_x_days with today's date."""
        today = datetime.now().isoformat()
        assert app.is_not_within_last_x_days(today, 3) is False

    def test_date_with_timezone_info(self):
        """Test date functions with timezone information."""
        # Date with timezone
        date_with_tz = "2023-01-01T00:00:00.0000000Z"
        # Mock datetime.now to return a specific date for testing
        with patch("app.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 5, 12, 0, 0)
            # 4 days difference
            assert app.is_within_last_x_days(date_with_tz, 7) is True
            assert app.is_not_within_last_x_days(date_with_tz, 3) is True
