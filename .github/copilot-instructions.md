# GitHub Copilot Instructions for Jellyfin Telegram Notifier

## Project Overview

This is a Flask-based webhook application that sends Telegram notifications when new media content (movies, series, seasons, episodes) is added to a Jellyfin media server. The application is designed to run as a Docker container with Gunicorn as the WSGI server.

## Tech Stack

- **Language**: Python 3.11
- **Framework**: Flask 3.0.0
- **WSGI Server**: Gunicorn 21.2.0
- **Deployment**: Docker (python:3.11-slim-bookworm)
- **Key Libraries**: requests, python-dotenv
- **APIs**: Telegram Bot API, Jellyfin API, YouTube Data API v3 (optional)

## Architecture and Design Patterns

### Application Structure

- **Single-file application**: All logic is contained in `app.py`
- **Entry point**: Flask webhook at `/webhook` endpoint
- **State management**: JSON file-based persistence for tracking notified items
- **Logging**: TimedRotatingFileHandler with daily rotation, 7-day retention

### Key Components

1. **Webhook Handler** (`/webhook` POST endpoint)
   - Receives Jellyfin webhook payloads
   - Processes Movie, Season, and Episode item types
   - Implements deduplication logic to avoid repeat notifications

2. **Notification System**
   - Sends formatted Telegram messages with images
   - Uses Markdown formatting for messages
   - Fetches images from Jellyfin server
   - Falls back to series/season images when specific images unavailable

3. **Filtering Logic**
   - Episodes: Only notifies if premiered within configurable days (`EPISODE_PREMIERED_WITHIN_X_DAYS`)
   - Seasons: Skips episode notifications if season added within configurable days (`SEASON_ADDED_WITHIN_X_DAYS`)
   - Prevents notification spam when bulk-adding seasons

4. **External API Integration**
   - Jellyfin API: Fetches item details and images
   - Telegram Bot API: Sends photo messages
   - YouTube API: Optional trailer URL fetching for movies

## Coding Standards and Best Practices

### Python Style

- Use descriptive function names with underscores (snake_case)
- Keep functions focused on single responsibilities
- Use f-strings for string formatting
- Include comprehensive logging for debugging and monitoring
- Handle exceptions gracefully with specific error messages

### Error Handling

- Catch `HTTPError` specifically for API call failures
- Use generic `Exception` catch-all as fallback
- Log all errors with context information
- Return descriptive error messages from webhook endpoint

### Configuration

- All configuration via environment variables
- Required variables: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `JELLYFIN_BASE_URL`, `JELLYFIN_API_KEY`, `YOUTUBE_API_KEY`, `EPISODE_PREMIERED_WITHIN_X_DAYS`, `SEASON_ADDED_WITHIN_X_DAYS`
- Use `python-dotenv` for local development
- Docker deployment uses environment variables passed via docker-compose

### Data Persistence

- Use JSON file at `/app/data/notified_items.json` for tracking sent notifications
- Format: `{item_type}:{item_name}:{release_year}` as keys
- Implement LRU-style cleanup (max 100 entries)
- Always save to disk after modifications

### Docker Considerations

- Run as non-root user (`pythonapp`)
- Mount volumes for logs (`/app/log`) and data (`/app/data`)
- Expose port 5000
- Set `PYTHONUNBUFFERED=1` for real-time logging

## Important Implementation Details

### Image Handling

- Primary source: Item-specific images from Jellyfin
- Fallback strategy: Season → Series for episodes; Series for seasons
- Always download images from Jellyfin, then upload to Telegram
- Images sent as `sendPhoto` with caption (not embedded URLs)

### Date/Time Logic

- Use ISO 8601 format for all date comparisons
- Extract date portion with `.split("T")[0]`
- Compare dates as strings (ISO format allows lexicographic comparison)
- `is_within_last_x_days()`: Check if date is recent enough
- `is_not_within_last_x_days()`: Check if date is old enough

### Notification Message Formats

**Movies**:
```
*🍿New Movie Added🍿*

*{movie_name}* *({year})*

{overview}

Runtime
{runtime}

[🎥][Trailer]({trailer_url})
```

**Seasons**:
```
*New Season Added*

*{series_name}* *({year})*

*{season_name}*

{overview}
```

**Episodes**:
```
*New Episode Added*

*Release Date*: {premiere_date}

*Series*: {series_name} *S*{season}*E*{episode}
*Episode Title*: {episode_name}

{overview}
```

### Deduplication Strategy

- Track notifications using composite key: `{item_type}:{item_name}:{release_year}`
- Check before sending notification
- Mark as notified after successful send
- Maintain max 100 entries with oldest-first cleanup

## Common Operations

### Adding New Item Types

1. Add new condition in webhook handler
2. Extract relevant fields from payload
3. Implement notification message format
4. Handle image fetching with appropriate fallbacks
5. Add deduplication check
6. Log the notification event

### Modifying Notification Logic

- Update filtering functions (`is_within_last_x_days`, etc.)
- Consider impact on existing configurations
- Test with various date scenarios
- Update environment variable documentation

### API Integration Changes

- All API calls use `requests` library
- Include headers and params as separate arguments
- Use `raise_for_status()` for automatic error checking
- Handle response JSON with `.get()` for safe access

## Testing Considerations

- No formal test suite currently exists
- Manual testing via Jellyfin webhook trigger
- Test with all item types: Movie, Season, Episode
- Verify notification deduplication
- Test image fallback scenarios
- Check log file rotation

## Docker and Deployment

### Building

```bash
docker build -t jellyfin-telegram-notifier .
```

### Running

```bash
docker-compose up
```

### Environment Setup

1. Copy `env.example` to `.env`
2. Fill in required API keys and tokens
3. Configure day thresholds for filtering

## Security Considerations

- Never commit `.env` file (git ignored)
- API keys and tokens via environment variables only
- Example values in `env.example` are placeholders
- Run container as non-root user
- No authentication on webhook endpoint (trust network security)

## Logging and Monitoring

- Logs location: `/app/log/jellyfin_telegram-notifier.log`
- Daily rotation with 7-day retention
- Log level: INFO
- Key events logged:
  - Successful notifications sent
  - Duplicate notification attempts
  - Filtered notifications (date-based)
  - Image fallback usage
  - Errors and HTTP failures

## Future Enhancement Ideas

When suggesting improvements, consider:
- Adding health check endpoint
- Implementing webhook authentication
- Supporting additional Jellyfin item types
- Adding message templates/customization
- Metrics and monitoring integration
- Unit and integration tests
- Configuration validation on startup
- Multi-language support for notifications
- Database instead of JSON file for state
