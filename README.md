# Jellyfin Notification System

A simple Flask application that sends notifications to Telegram whenever new content (movies, series, seasons, episodes) is added to Jellyfin.

---

## Features

- Sends Telegram notifications with media images whenever a new movie, series, season, or episode is added to Jellyfin.
- Integrates with the Jellyfin webhook plugin.
- Provides a filter to notify only for recent episodes or newly added seasons.
- Supports multiple architectures: amd64 and arm64 (aarch64).

## Prerequisites

- A Jellyfin server with the Webhook plugin installed.
- A Telegram bot token and chat ID (see the section on setting up a Telegram bot below).
- Docker (optional, for Docker installation).

## Installation

### Traditional Installation

1. Clone the repository.
2. Install the requirements using `pip install -r requirements.txt`.
3. Set up your environment variables. (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, JELLYFIN_BASE_URL, JELLYFIN_API_KEY, YOUTUBE_API_KEY, EPISODE_PREMIERED_WITHIN_X_DAYS, SEASON_ADDED_WITHIN_X_DAYS).
4. Run the application using `python3 main.py`.

### Docker Installation

If you have Docker and Docker Compose installed, you can use the provided `docker-compose.yml`

1. Set up your environment variables in a `.env` file.
2. Run `docker-compose up`.

### Build and Push Script

The repository includes a bash script (`build-and-push.sh`) that automates the process of building and pushing Docker images to a local registry. This script:

1. Downloads the latest version of the repository using GitHub CLI (or falls back to git clone)
2. Builds the Docker image
3. Applies multiple tags (latest, version, commit hash)
4. Pushes the image to a local Docker registry

**Prerequisites:**
- GitHub CLI (`gh`) installed (optional, will fallback to git if not authenticated)
- Docker installed
- Local Docker registry running (e.g., `docker run -d -p 5000:5000 --name registry registry:2`)

**Usage:**
```bash
# Run the full build and push process
./build-and-push.sh

# Test without actually building or pushing (dry-run mode)
./build-and-push.sh --dry-run

# Show help
./build-and-push.sh --help
```

The script will create tags for:
- `localhost:5000/jellyfin-telegram-notifier:latest`
- `localhost:5000/jellyfin-telegram-notifier:<version>`
- `localhost:5000/jellyfin-telegram-notifier:<commit-hash>`

## Setting Up a Telegram Bot

1. Start a Chat with BotFather on Telegram.
2. Send `/newbot` command.
3. Name your bot.
4. Choose a unique username for your bot; it must end in `bot`.
5. Retrieve your HTTP API token.
6. Get your chat ID by starting a chat with your bot, sending a message, then visiting `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates` to find the chat ID in the returned JSON.
7. Input the Bot Token and Chat ID into the application's environment variables.

## Usage

### Setting up Jellyfin Webhook

1. Go to Jellyfin dashboard.
2. Navigate to `Plugins`.
3. Choose `Webhook` and add a new webhook.
4. Set the server to the Flask application's endpoint (e.g., `http://localhost:5000/webhook`).
5. For `Notification Type`, select `Item Added`.
6. For `Item Type`, select `Movie, Episode, Season`.
7. Make sure to enable the `Send All Properties (ignores template)` option.

#### Environment Variables Explanation:

- **`PUID`** (Docker only, default: 1000):
  User ID for the application to run as. Set this to match your host user's UID to avoid permission issues with mounted volumes.

- **`PGID`** (Docker only, default: 1000):
  Group ID for the application to run as. Set this to match your host user's GID to avoid permission issues with mounted volumes.

- **`UMASK`** (Docker only, default: 002):
  Controls the default file creation permissions. A value of `002` allows group write access, while `022` restricts write access to the owner only.

- **`TZ`** (Docker only, default: Etc/UTC):
  Timezone for the container. Examples: `America/New_York`, `Europe/London`, `Asia/Tokyo`.

- **`EPISODE_PREMIERED_WITHIN_X_DAYS`**:
  Determines how recent an episode's premiere date must be for a notification to be sent. For example, setting it to `7` means only episodes that premiered within the last 7 days will trigger a notification.

- **`SEASON_ADDED_WITHIN_X_DAYS`**:
  Dictates the threshold for sending notifications based on when a season was added to Jellyfin. If set to `3`, then if a season was added within the last 3 days, episode notifications will not be sent to avoid potential spam from adding an entire season at once.

## Notification Logic

This section provides a detailed explanation of when notifications are and are not sent for each item type.

### Movie Notifications

**When a notification IS sent:**
- The item type is "Movie"
- The movie has NOT been previously notified (deduplication check)

**When a notification is NOT sent:**
- The movie was already notified previously

### Season Notifications

**When a notification IS sent:**
- The item type is "Season"
- The season has NOT been previously notified (deduplication check)

**When a notification is NOT sent:**
- The season was already notified previously

**Note:** Season notifications are sent immediately without any date-based filtering. There is no check on when the season was created or any premiere date filtering for seasons.

### Episode Notifications

Episode notifications have the most complex filtering logic, designed to prevent notification spam when bulk-adding content.

**When a notification IS sent:**
All of the following conditions must be true:
1. The item type is "Episode"
2. The episode has NOT been previously notified (deduplication check)
3. The season was added **more than** `SEASON_ADDED_WITHIN_X_DAYS` days ago (the season was NOT recently added to Jellyfin)
4. The episode's `PremiereDate` exists AND is **within the last** `EPISODE_PREMIERED_WITHIN_X_DAYS` days

**When a notification is NOT sent:**
- The episode was already notified previously, OR
- The season was added within the last `SEASON_ADDED_WITHIN_X_DAYS` days (prevents spam when adding an entire season at once), OR
- The episode's premiere date is older than `EPISODE_PREMIERED_WITHIN_X_DAYS` days, OR
- The episode has no premiere date set

### Episode Filtering Explained

The episode filtering uses two environment variables that work together:

1. **`SEASON_ADDED_WITHIN_X_DAYS`** (default: 3)
   - If a season was added to Jellyfin within this many days, ALL episode notifications for that season are suppressed
   - This prevents receiving dozens of notifications when you add an entire season at once
   - Example: If set to `3`, and you add Season 1 today, episode notifications for that season will be suppressed because the season's `DateCreated` is less than 3 days ago

2. **`EPISODE_PREMIERED_WITHIN_X_DAYS`** (default: 7)
   - Only episodes that premiered within this many days will trigger notifications
   - This ensures you only get notified about recent/new episodes, not old ones
   - Example: If set to `7`, an episode that premiered 10 days ago will NOT trigger a notification

### Decision Flow for Episodes

```
Episode Webhook Received
        │
        ▼
┌───────────────────────────┐
│ Was this episode already  │
│ notified?                 │
└───────────────────────────┘
        │
    Yes │           No
        ▼           │
   [No Action]      ▼
              ┌───────────────────────────┐
              │ Was the season added      │
              │ within SEASON_ADDED_      │
              │ WITHIN_X_DAYS?            │
              └───────────────────────────┘
                      │
                  Yes │           No
                      ▼           │
                 [No Action -     ▼
                  Spam           ┌───────────────────────────┐
                  Prevention]    │ Did the episode premiere  │
                                 │ within EPISODE_PREMIERED_ │
                                 │ WITHIN_X_DAYS?            │
                                 └───────────────────────────┘
                                         │
                                     Yes │           No
                                         ▼           │
                                    [Send           ▼
                                     Notification] [No Action - Old Episode]
```

### Common Scenarios

| Scenario | Notification Sent? | Reason |
|----------|-------------------|--------|
| New movie added | ✅ Yes | Movies are always notified (unless duplicate) |
| New season added | ✅ Yes | Seasons are always notified (unless duplicate) |
| New episode added, season is new, episode premiered today | ❌ No | Season was added within `SEASON_ADDED_WITHIN_X_DAYS` |
| New episode added, season is old, episode premiered today | ✅ Yes | All conditions met |
| New episode added, season is old, episode premiered 30 days ago | ❌ No | Episode premiere date is too old |
| Same movie/season/episode added again | ❌ No | Already notified (deduplication) |

### Deduplication

The application tracks all sent notifications using a composite key format: `{ItemType}:{ItemName}:{Year}`. For example:
- Movie: `Movie:The Matrix:1999`
- Season: `Season:Season 1:2023`
- Episode: `Episode:Pilot:2023` (Note: Episode name is typically unique within a series)

This prevents duplicate notifications for the same item. The tracking file is stored at `/app/data/notified_items.json` and maintains a maximum of 100 entries (oldest entries are automatically removed when the limit is exceeded).

### Setting Up YouTube API Key (Optional)

If you want to fetch YouTube trailer URLs for movies, you can set up a YouTube API key:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or use an existing one.
3. Enable the "YouTube Data API v3" for your project.
4. Create credentials for your project:
   - Go to the "Credentials" tab.
   - Click on "Create Credentials" and select "API Key".
5. Copy the generated API key.
6. Set the `YOUTUBE_API_KEY` environment variable in your `.env` file to the copied API key.

## CI/CD and Multi-Architecture Support

This project includes a GitHub Actions workflow that automatically builds and validates the Docker image for multiple architectures:

- **Supported Platforms**: linux/amd64, linux/arm64 (aarch64)
- **Workflow Triggers**: Push to main/develop branches, pull requests, and manual dispatch
- **Build Process**: Uses Docker Buildx with QEMU for cross-platform builds

The CI workflow ensures that the Docker image can be successfully built for both x86_64 and ARM64 architectures, making it compatible with a wide range of devices including Raspberry Pi, AWS Graviton instances, and Apple Silicon Macs.

## Testing

This project includes a comprehensive test suite with unit and integration tests covering all major functionality.

### Running Tests Locally

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run all tests:
   ```bash
   pytest tests/ -v
   ```

3. Run tests with coverage report:
   ```bash
   pytest tests/ -v --cov=app --cov-report=term-missing
   ```

4. Run specific test files:
   ```bash
   pytest tests/test_date_filtering.py -v
   pytest tests/test_notification_tracking.py -v
   pytest tests/test_api_integration.py -v
   pytest tests/test_webhook.py -v
   ```

### Linting

The project uses flake8 and black for code quality:

1. Check code style with flake8:
   ```bash
   flake8 app.py tests/
   ```

2. Format code with black:
   ```bash
   black --line-length 120 app.py tests/
   ```

### Test Coverage

The test suite provides 98% code coverage including:
- Date filtering functions
- Notification tracking and deduplication
- Jellyfin, Telegram, and YouTube API integrations
- Webhook endpoint for all item types (Movie, Season, Episode)
- Error handling and edge cases

### Testing the Webhook Endpoint

The repository includes a bash script (`test-webhook.sh`) that can be used to test the running application by sending sample webhook calls. This is useful for verifying that notifications are properly sent to Telegram.

**Prerequisites:**
- `curl` installed
- `jq` installed (optional, for pretty JSON formatting)
- The application running and accessible

**Usage:**
```bash
# Test all item types (movie, season, episode)
./test-webhook.sh

# Test a specific item type
./test-webhook.sh --type movie
./test-webhook.sh --type season
./test-webhook.sh --type episode

# Test with a custom webhook URL
./test-webhook.sh --url http://192.168.1.100:5000/webhook

# Show help
./test-webhook.sh --help
```

The script includes comprehensive example payloads with all optional attributes for each item type:
- **Movie**: Includes runtime, overview, genres, ratings, providers (TMDB, IMDB), video/audio codecs, and more
- **Season**: Includes series information, overview, episode count, premiere date, and metadata
- **Episode**: Includes series/season details, episode numbers, premiere date, runtime, and full media information

After running the script, check your Telegram chat to verify that notifications were received with the correct formatting and images.

### CI/CD

The project uses GitHub Actions for continuous integration:
- Automated testing on Python 3.11 and 3.12
- Code linting and formatting checks
- Code coverage reporting
- Multi-architecture Docker builds

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests for new features, bug fixes, or improvements.

When contributing, please:
- Write tests for new features
- Ensure all tests pass with `pytest tests/`
- Run linting with `flake8 app.py tests/`
- Format code with `black --line-length 120 app.py tests/`

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
