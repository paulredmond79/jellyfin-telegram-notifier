# GitHub Copilot Instructions for Jellyfin Telegram Notifier

## Project Overview

A Flask-based webhook application that sends rich Telegram notifications with media images when new content (movies, series, seasons, episodes) is added to a Jellyfin media server. Features automatic library detection and "Leaving Soon" warning support. Designed to run as a Docker container with Gunicorn as the WSGI server.

## Tech Stack

- **Language**: Python 3.14+ (tested on 3.11, 3.12, 3.14)
- **Framework**: Flask 3.0.0
- **WSGI Server**: Gunicorn 21.2.0
- **Deployment**: Docker (python:3.11-slim-bookworm)
- **Key Libraries**: requests, python-dotenv, flasgger (Swagger/OpenAPI docs)
- **APIs**: Jellyfin API, Telegram Bot API, YouTube Data API v3 (optional)
- **Testing**: pytest 7.4.4+, pytest-cov, pytest-flask, pytest-mock

## Architecture and Design Patterns

### Application Structure

- **Single-file architecture**: All logic contained in `app.py` (~700 lines)
- **Entry point**: Flask webhook at `/webhook` POST endpoint
- **Documentation**: Swagger UI at `/docs` (auto-generated from docstrings)
- **State management**: JSON file-based persistence at `/app/data/notified_items.json`
- **Logging**: TimedRotatingFileHandler with daily rotation and 7-day retention
- **HTTP Client**: Configured requests Session with automatic retry logic (3 retries, exponential backoff)

### Key Components

1. **Webhook Handler** (`/webhook` POST endpoint)
   - Receives Jellyfin webhook payloads with item metadata
   - Processes Movie, Season, and Episode item types
   - Implements request validation and error handling
   - Returns appropriate HTTP responses and error messages

2. **Library Detection System**
   - Fetches parent collection/library information via Jellyfin API
   - Extracts library name from item parent ID
   - Caches results to avoid redundant API calls
   - Detects "Leaving Soon" libraries (case-insensitive matching)
   - Gracefully degrades if library fetch fails

3. **Notification System**
   - Downloads images from Jellyfin media server
   - Sends formatted Telegram messages with images via Telegram Bot API
   - Uses Telegram Markdown formatting (V1) for text styling
   - Falls back to series/season images when specific images unavailable
   - Includes library name and "Leaving Soon" warnings when applicable

4. **Content Filtering Logic**
   - Episodes: Only notifies if premiered within `EPISODE_PREMIERED_WITHIN_X_DAYS`
   - Seasons: Skips episode notifications if season added within `SEASON_ADDED_WITHIN_X_DAYS`
   - Prevents notification spam from bulk season/episode additions
   - Uses ISO 8601 date string comparisons (lexicographic)

5. **Notification Deduplication**
   - Tracks sent notifications with composite key: `{item_type}:{item_name}:{release_year}`
   - Prevents duplicate notifications for the same item
   - Implements LRU-style cleanup (maintains max 100 entries)
   - Persists state to JSON file after each notification

6. **External API Integration**
   - **Jellyfin API**: Fetches item details, images, and library information
   - **Telegram Bot API**: Sends photo messages with Markdown captions
   - **YouTube API** (optional): Searches for and fetches movie trailer URLs

## Configuration and Environment Variables

### Required Variables

All of these must be configured for the application to function:

- **`TELEGRAM_BOT_TOKEN`**: Telegram bot token from BotFather (format: `123456:ABC-DEF1234...`)
- **`TELEGRAM_CHAT_ID`**: Target chat ID for notifications (can be user ID or group ID)
- **`JELLYFIN_BASE_URL`**: Internal Jellyfin server URL used for API calls (e.g., `http://192.168.1.100:8096`)
- **`JELLYFIN_API_KEY`**: Jellyfin API key for authentication (obtained from Jellyfin Dashboard)
- **`EPISODE_PREMIERED_WITHIN_X_DAYS`**: Integer; only notify for episodes premiered within this many days
- **`SEASON_ADDED_WITHIN_X_DAYS`**: Integer; if season added within this many days, skip episode notifications

### Optional Variables

- **`JELLYFIN_EXTERNAL_URL`** (Default: same as `JELLYFIN_BASE_URL`): Public URL shown in "Watch Now" links in notifications. Use different internal/external URLs if behind NAT/proxy.
- **`YOUTUBE_API_KEY`**: YouTube Data API key for fetching movie trailer links. If not set, trailers are omitted from notifications.
- **`LOG_DIRECTORY`** (Default: `/app/log`): Directory for application logs
- **`NOTIFIED_ITEMS_FILE`** (Default: `/app/data/notified_items.json`): Path to JSON file tracking sent notifications

### Docker-Only Variables

- **`PUID`** (Default: 1000): User ID for application process (set to match host user for volume permissions)
- **`PGID`** (Default: 1000): Group ID for application process (set to match host group for volume permissions)
- **`UMASK`** (Default: 002): File creation mask (002 = group writable, 022 = owner only)
- **`TZ`** (Default: Etc/UTC): Container timezone (e.g., `America/New_York`, `Europe/London`)

### Configuration Pattern

Environment variables are loaded at startup via `python-dotenv`. Use `.env` file for local development:

```env
# Required - Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_CHAT_ID=987654321

# Required - Jellyfin (Internal)
JELLYFIN_BASE_URL=http://192.168.1.100:8096
JELLYFIN_API_KEY=abcdef1234567890abcdef1234567890

# Optional - Jellyfin (External, for notifications)
JELLYFIN_EXTERNAL_URL=https://jellyfin.example.com

# Required - Filtering
EPISODE_PREMIERED_WITHIN_X_DAYS=7
SEASON_ADDED_WITHIN_X_DAYS=3

# Optional
YOUTUBE_API_KEY=AIzaSyD_...
LOG_DIRECTORY=/app/log
NOTIFIED_ITEMS_FILE=/app/data/notified_items.json
```

## Coding Standards and Best Practices

### Python Style Guide

- Use snake_case for functions and variables, PascalCase for classes
- Prefer descriptive names: `extract_library_name()` over `get_lib()`
- Keep functions focused on single responsibility (max ~50 lines for clarity)
- Use f-strings for all string formatting
- Type hints optional but encouraged for complex functions
- Docstrings for helper functions explaining behavior and error handling

### Code Formatting Requirements

**Black Formatting (REQUIRED for CI/CD)**:
- All Python code must pass Black formatting checks with **120 character line length**
- GitHub Actions will fail if code is not properly formatted
- Must run this before pushing commits:
  ```bash
  black --line-length 120 app.py tests/
  ```
- To verify formatting without changes:
  ```bash
  black --check --line-length 120 app.py tests/
  ```
- If you see `reformat` messages, run the formatter and commit the changes
- Common formatting issues:
  - Long function signatures that exceed 120 chars (wrap parameters to next lines)
  - Long strings that exceed 120 chars (move to f-strings with proper breaks)
  - Method decorators with multiple parameters (wrap to multiple lines)
  - Long conditional blocks (break into multiple conditions)

### Error Handling Strategy

- Catch `HTTPError` for API-specific failures
- Catch `RequestException` for network-level failures
- Use `Exception` catch-all as final fallback
- Log error context: what operation failed, why, and recovery action
- Return user-friendly error messages from webhook endpoint
- Never raise exceptions from webhook handler; always return HTTP response

### API Request Standards

All external API calls use the configured `http_session` with:
- **Timeout**: 30 seconds for regular requests, 60 seconds for image downloads
- **Retries**: 3 automatic retries for status codes [429, 500, 502, 503, 504]
- **Headers**: Include `accept: application/json` where applicable
- **Parameters**: Pass API keys as query parameters, not headers
- **Response Handling**: Call `.raise_for_status()` then safe access with `.get()`

Example pattern:
```python
headers = {"accept": "application/json"}
params = {"api_key": JELLYFIN_API_KEY}
response = http_session.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
response.raise_for_status()
data = response.json()
```

### Data Persistence

- JSON file persistence at `/app/data/notified_items.json`
- Key format: `{item_type}:{item_name}:{release_year}` (must be unique)
- Load on startup with `load_notified_items()`, save after modifications
- Cleanup strategy: When entries exceed 100, delete oldest entries first
- Ensure data directory exists before writing

### Image Handling Strategy

- **Primary source**: Item-specific images from Jellyfin (`/Items/{itemId}/Images/Primary`)
- **Fallback cascade**: 
  - For episodes: Season image → Series image
  - For seasons: Series image
  - For movies: No fallback (images are required)
- **Download then upload**: Download from Jellyfin, then upload to Telegram (never use URLs)
- **Format**: Always send as JPEG via `sendPhoto` with caption

### Date/Time Logic

- **Format**: All dates in ISO 8601 format (`YYYY-MM-DD` for comparisons)
- **Extraction**: Use `.split("T")[0]` to extract date portion from timestamps
- **Comparison**: Since ISO 8601 is lexicographically sortable, string comparison is safe
- **Functions**:
  - `is_within_last_x_days(date_str, x)`: Returns True if date is recent
  - `is_not_within_last_x_days(date_str, x)`: Returns True if date is old

## Feature Implementation Details

### Library Detection and "Leaving Soon" Support

**Purpose**: Inform users when content will be removed from Jellyfin, and display which library items belong to.

**Implementation Flow**:
1. When webhook received with ItemId, fetch full item details: `get_item_details(item_id)`
2. Extract ParentId from item details
3. Fetch parent (library) details: `get_item_details(parent_id)`
4. Extract library name from parent item
5. Check if library name contains "leaving soon" (case-insensitive)
6. If leaving soon library, add warning header and removal notice to notification

**Helper Functions**:
- `extract_library_name(item_details)`: Returns library name or None
- `is_leaving_soon_library(library_name)`: Case-insensitive "leaving soon" check

**Notification Modifications**:
- Add "⚠️ *LEAVING SOON* ⚠️" header if applicable
- Display library name: "*Library*: {library_name}"
- Add warning: "⚠️ This movie/show will be removed soon!"
- Graceful degradation: If library fetch fails, notification still sent without library info

### Notification Message Formats

**Format with Library Info (Normal Library)**:
```
*🍿New Movie Added🍿*

*{movie_name}* *({year})*

{overview}

Runtime
{runtime}

*Library*: {library_name}

[🎥]({trailer_url})[Trailer]({trailer_url})
[▶️ Watch Now]({external_url})
```

**Format with Leaving Soon Warning**:
```
⚠️ *LEAVING SOON* ⚠️

*🍿New Movie Added🍿*

*{movie_name}* *({year})*

{overview}

Runtime
{runtime}

*Library*: Leaving Soon

⚠️ This movie will be removed soon!

[🎥]({trailer_url})[Trailer]({trailer_url})
[▶️ Watch Now]({external_url})
```

**Season Format**:
```
[⚠️ *LEAVING SOON* ⚠️]

*New Season Added*

*{series_name}* *({year})*

*{season_name}*

{overview}

[*Library*: {library_name}]

[⚠️ This show will be removed soon!]

[▶️ Watch Now]({external_url})
```

**Episode Format**:
```
[⚠️ *LEAVING SOON* ⚠️]

*New Episode Added*

*Release Date*: {premiere_date}

*Series*: {series_name} *S*{season}*E*{episode}
*Episode Title*: {episode_name}

{overview}

[*Library*: {library_name}]

[⚠️ This show will be removed soon!]

[▶️ Watch Now]({external_url})
```

### Internal vs External URLs

**Purpose**: Allow different URLs for internal API calls vs public user-facing links.

**Usage**:
- `JELLYFIN_BASE_URL`: Used for all Jellyfin API calls and image downloads
- `JELLYFIN_EXTERNAL_URL`: Used in notification "Watch Now" links
- If `JELLYFIN_EXTERNAL_URL` not set, defaults to `JELLYFIN_BASE_URL`

**Example Scenario**:
```
Internal (Docker): http://jellyfin:8096 (container DNS)
External (User): https://jellyfin.example.com (public HTTPS)

JELLYFIN_BASE_URL=http://jellyfin:8096
JELLYFIN_EXTERNAL_URL=https://jellyfin.example.com

API calls → http://jellyfin:8096 (fast, internal)
Notifications → https://jellyfin.example.com (public link)
```

## Testing Strategy and Standards

### Test Organization

- **Test Framework**: pytest with pytest-flask, pytest-mock
- **Location**: `tests/` directory with organized test modules
- **Fixtures**: Centralized in `conftest.py` for reusability
- **Coverage Target**: 80%+ line coverage with meaningful assertions

### Test Module Organization

1. **`test_api_integration.py`**: API interaction tests
   - Jellyfin API calls with mocked responses
   - YouTube API integration
   - Telegram API integration
   - HTTP session and retry configuration
   - **New**: Library detection functions

2. **`test_webhook.py`**: Webhook endpoint integration tests
   - Movie/Season/Episode notifications
   - Image fallback scenarios
   - Deduplication logic
   - **New**: Leaving Soon detection
   - URL usage (external vs internal)
   - Error handling

3. **`test_date_filtering.py`**: Date-based filtering logic
   - `is_within_last_x_days()` boundary conditions
   - `is_not_within_last_x_days()` logic
   - ISO 8601 date format handling

4. **`test_notification_tracking.py`**: Deduplication and state management
   - Load/save notified items from JSON
   - Key composition and uniqueness
   - Max entries cleanup logic
   - Thread-safety considerations

5. **`test_swagger.py`**: API documentation validation
   - Swagger endpoint availability
   - OpenAPI spec generation
   - Endpoint documentation presence

### Test Fixtures (`conftest.py`)

Centralized fixtures for:
- Environment variables
- Flask test client
- Sample webhook payloads (movie, season, episode)
- Mock Jellyfin API responses (with and without leaving soon)
- Mock Telegram API responses
- Temporary file management

Key example:
```python
@pytest.fixture
def sample_movie_payload():
    """Jellyfin webhook payload for movie"""
    return {
        "ItemType": "Movie",
        "ItemId": "movie123",
        "Name": "Test Movie",
        "Year": 2023,
        "Overview": "...",
        "RunTime": "02:00:00",
    }

@pytest.fixture
def mock_jellyfin_leaving_soon_library_details():
    """Mock response for leaving soon library query"""
    return {
        "Items": [{
            "Id": "lib123",
            "Name": "Leaving Soon",
        }]
    }
```

### Testing Best Practices

- Use `@patch` decorators to mock external API calls
- Verify both happy path and error scenarios
- Test message formatting includes all expected content
- Verify external URLs are used in notifications, not internal ones
- Test graceful degradation (e.g., missing library info)
- Use `side_effect` for sequential mock responses
- Assert correct error handling and messages returned

### Running Tests Locally

```bash
# All tests with coverage
pytest -v --cov=app --cov-report=term-missing

# Specific test class
pytest tests/test_webhook.py::TestWebhookMovie -v

# With detailed output
pytest -vv -s

# Show slowest tests
pytest --durations=10
```

**Current Test Suite**: 74 tests, 84% code coverage

## Docker and Deployment

### Docker Build Strategy

- **Image**: `python:3.11-slim-bookworm` (minimal, security-focused)
- **Non-root user**: Creates `pythonapp` user for security
- **Volumes**:
  - `/app/log`: Application logs
  - `/app/data`: JSON state file
- **Port**: 5000 (Flask default)
- **Environment**: `PYTHONUNBUFFERED=1` for real-time logging

### Build and Deployment

```bash
# Build
docker build -t jellyfin-telegram-notifier .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

### Multi-Architecture Support

- **Supported**: linux/amd64, linux/arm64 (aarch64)
- **CI/CD**: GitHub Actions with Docker Buildx
- **Use Cases**: Standard servers, Raspberry Pi, AWS Graviton, Apple Silicon

### Volume Mounting

Ensure docker-compose mounts have correct permissions:

```yaml
volumes:
  - ./log:/app/log          # Logs with PUID:PGID ownership
  - ./data:/app/data        # State files with PUID:PGID ownership
```

## Security Considerations

- **Environment Variables**: Never commit `.env` (included in `.gitignore`)
- **API Keys**: Passed via environment only, never hardcoded
- **Webhook Authentication**: None required (assumes trusted network)
- **Non-root Docker**: Container runs as unprivileged `pythonapp` user
- **Image Downloads**: Always download then re-upload (never hotlink)
- **Log Sanitization**: Avoid logging sensitive data (API keys, tokens)

## Logging and Monitoring

### Log Configuration

- **Location**: `/app/log/jellyfin_telegram-notifier.log`
- **Rotation**: Daily rotation, 7-day retention
- **Level**: INFO (debug details for important operations)
- **Format**: `%(asctime)s - %(levelname)s - %(message)s`

### Key Events Logged

- **Successful notifications**: Item type, name, year, destination
- **Duplicate prevention**: When item already notified, reason
- **Filtered items**: Episodes/seasons filtered by date, reason
- **Image fallbacks**: When primary image failed, fallback used
- **Library detection**: Library name extracted, "Leaving Soon" status
- **Errors**: Detailed error messages with HTTP status codes

### Example Log Entries

```
2024-03-03 10:30:45 - INFO - (Movie) The Matrix 1999 notification was sent to telegram.
2024-03-03 10:31:12 - INFO - (Movie) Inception Notification Was Already Sent
2024-03-03 10:32:00 - WARNING - (Season) Breaking Bad Season 1 image does not exist (status: 404), falling back to series image
2024-03-03 10:33:45 - INFO - (Episode) Breaking Bad S05E16 notification sent to Telegram!
2024-03-03 10:34:30 - WARNING - Failed to fetch library information for movie The Matrix: API Error
```

## Common Development Tasks

### Pre-Commit Checklist

Before pushing any code, ensure all checks pass locally:

```bash
# 1. Format code with Black (120 char line length)
black --line-length 120 app.py tests/

# 2. Run flake8 syntax checks
flake8 app.py --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 app.py tests/ --count --exit-zero --max-complexity=10 --statistics

# 3. Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# If all pass locally, safe to push!
git push
```

This mirrors the exact GitHub Actions workflow, preventing surprises.

### Adding New Features

1. **Identify component**: Where does it fit? (webhook handler, notification, filtering)
2. **Implement function**: Follow coding standards, add error handling
3. **Add logging**: Log key decisions and errors
4. **Write tests first**: Add unit tests in appropriate test module
5. **Test manually**: Run full test suite, verify with actual webhook
6. **Update docs**: README, env.example, docstrings

### Modifying Notification Templates

1. Update message construction in webhook handler
2. Add/remove fields in notification format
3. Update notification message format documentation (this file)
4. Add tests for new message content in `test_webhook.py`
5. Test with different item types (movie, season, episode)

### Adding API Integration

1. Create new helper function following API standards
2. Use `http_session` (with retries), not raw `requests`
3. Include timeout and error handling
4. Add test cases in `test_api_integration.py`
5. Test with both success and failure scenarios

### Database or State Changes

1. Currently uses JSON file persistence
2. If migrating to database: Update `load_notified_items()` and `save_notified_items()`
3. Maintain same interface for backward compatibility
4. Update tests for new persistence layer

## Future Enhancement Ideas

When suggesting improvements, consider:

- **Health check endpoint**: `/health` endpoint for monitoring
- **Webhook authentication**: Signature verification for security
- **Additional item types**: Movies, music, books (from Jellyfin)
- **Message customization**: User-defined notification templates
- **Metrics/monitoring**: Prometheus metrics, Grafana dashboards
- **Database backend**: Replace JSON with SQLite/PostgreSQL
- **Scheduled notifications**: Upcoming releases, expiring content
- **Multi-language support**: Localized notification messages
- **Configuration validation**: Startup checks for required values
- **Webhook signature verification**: HMAC-based security
- **Rate limiting**: Per-user notification throttling
- **Message threading**: Telegram topic/thread support

Always consider:
- **Backward compatibility**: Don't break existing configurations
- **Testing impact**: Add tests for new features
- **Documentation**: Update README and this file
- **Performance**: Check HTTP request counts and timeouts
- **Error handling**: Graceful degradation, informative logs

