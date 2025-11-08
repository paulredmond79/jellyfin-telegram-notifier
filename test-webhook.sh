#!/bin/bash

# Test Webhook Script for Jellyfin Telegram Notifier
# This script sends test webhook calls to the running application
# to verify that notifications are properly sent to Telegram
#
# Usage: ./test-webhook.sh [OPTIONS]
# Options:
#   --url <url>      Webhook URL (default: http://localhost:5000/webhook)
#   --type <type>    Item type to test: movie, season, episode, or all (default: all)
#   --help           Display this help message

set -e  # Exit on any error

# Configuration
WEBHOOK_URL="http://localhost:5000/webhook"
ITEM_TYPE="all"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            WEBHOOK_URL="$2"
            shift 2
            ;;
        --type)
            ITEM_TYPE="$2"
            shift 2
            ;;
        --help)
            echo "Test Webhook Script for Jellyfin Telegram Notifier"
            echo ""
            echo "Usage: ./test-webhook.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --url <url>      Webhook URL (default: http://localhost:5000/webhook)"
            echo "  --type <type>    Item type to test: movie, season, episode, or all (default: all)"
            echo "  --help           Display this help message"
            echo ""
            echo "Examples:"
            echo "  ./test-webhook.sh"
            echo "  ./test-webhook.sh --type movie"
            echo "  ./test-webhook.sh --url http://192.168.1.100:5000/webhook --type episode"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to send a webhook test
send_webhook() {
    local item_type=$1
    local payload=$2
    
    echo -e "${BLUE}Sending ${item_type} webhook test to ${WEBHOOK_URL}${NC}"
    echo -e "${YELLOW}Payload:${NC}"
    echo "$payload" | jq '.'
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$WEBHOOK_URL")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
        echo -e "${GREEN}Response: $body${NC}"
    else
        echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
        echo -e "${RED}Response: $body${NC}"
    fi
    echo ""
}

# Movie payload with all optional attributes
movie_payload='{
  "ItemType": "Movie",
  "Name": "The Matrix",
  "Year": 1999,
  "ItemId": "test-movie-matrix-1999",
  "Overview": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
  "RunTime": "02:16:00",
  "Provider_tmdb": "603",
  "Provider_imdb": "tt0133093",
  "Genre": ["Action", "Science Fiction"],
  "OfficialRating": "R",
  "CommunityRating": 8.7,
  "Path": "/media/movies/The Matrix (1999)/The Matrix (1999).mkv",
  "FileName": "The Matrix (1999).mkv",
  "DateCreated": "2024-01-15T10:30:00.0000000Z",
  "PremiereDate": "1999-03-31T00:00:00.0000000Z",
  "ProductionYear": 1999,
  "Studios": ["Warner Bros. Pictures", "Village Roadshow Pictures"],
  "Tags": ["sci-fi", "classic", "cyberpunk"],
  "Container": "mkv",
  "VideoCodec": "hevc",
  "AudioCodec": "aac",
  "Width": 1920,
  "Height": 1080,
  "AspectRatio": "16:9",
  "Framerate": 23.976,
  "VideoBitrate": 5000000,
  "AudioBitrate": 320000,
  "AudioChannels": 6,
  "AudioLanguages": ["eng"],
  "SubtitleLanguages": ["eng", "spa", "fre"],
  "FileSize": 4294967296
}'

# Season payload with all optional attributes
season_payload='{
  "ItemType": "Season",
  "Name": "Season 1",
  "Year": 2008,
  "ItemId": "test-season-breaking-bad-s01",
  "SeriesName": "Breaking Bad",
  "SeriesId": "test-series-breaking-bad",
  "Overview": "When chemistry teacher Walter White is diagnosed with Stage III cancer and given only two years to live, he decides he has nothing to lose. He lives with his teenage son, who has cerebral palsy, and his wife, in New Mexico. Determined to ensure that his family will have a secure future, Walt embarks on a career of drugs and crime.",
  "IndexNumber": 1,
  "ParentIndexNumber": 1,
  "Provider_tvdb": "81189",
  "Provider_imdb": "tt0959621",
  "Genre": ["Drama", "Crime", "Thriller"],
  "OfficialRating": "TV-MA",
  "CommunityRating": 9.0,
  "Path": "/media/tv/Breaking Bad/Season 01",
  "DateCreated": "2024-01-15T10:30:00.0000000Z",
  "PremiereDate": "2008-01-20T00:00:00.0000000Z",
  "ProductionYear": 2008,
  "Studios": ["AMC", "Sony Pictures Television"],
  "Tags": ["must-watch", "drama"],
  "EpisodeCount": 7,
  "RecursiveItemCount": 7
}'

# Episode payload with all optional attributes
episode_payload='{
  "ItemType": "Episode",
  "Name": "Pilot",
  "Year": 2008,
  "ItemId": "test-episode-breaking-bad-s01e01",
  "SeriesName": "Breaking Bad",
  "SeriesId": "test-series-breaking-bad",
  "SeasonId": "test-season-breaking-bad-s01",
  "EpisodeNumber": 1,
  "EpisodeNumber00": "01",
  "SeasonNumber": 1,
  "SeasonNumber00": "01",
  "Overview": "When an unassuming high school chemistry teacher discovers he has a rare form of lung cancer, he decides to team up with a former student and create a top of the line crystal meth in a used RV, to provide for his family once he is gone.",
  "RunTime": "00:58:00",
  "IndexNumber": 1,
  "ParentIndexNumber": 1,
  "Provider_tvdb": "349232",
  "Provider_imdb": "tt0959621",
  "Genre": ["Drama", "Crime"],
  "OfficialRating": "TV-MA",
  "CommunityRating": 8.5,
  "Path": "/media/tv/Breaking Bad/Season 01/Breaking Bad - S01E01 - Pilot.mkv",
  "FileName": "Breaking Bad - S01E01 - Pilot.mkv",
  "DateCreated": "2024-01-15T10:30:00.0000000Z",
  "PremiereDate": "2008-01-20T00:00:00.0000000Z",
  "ProductionYear": 2008,
  "Studios": ["AMC"],
  "Container": "mkv",
  "VideoCodec": "hevc",
  "AudioCodec": "aac",
  "Width": 1920,
  "Height": 1080,
  "AspectRatio": "16:9",
  "Framerate": 23.976,
  "VideoBitrate": 3000000,
  "AudioBitrate": 192000,
  "AudioChannels": 2,
  "AudioLanguages": ["eng"],
  "SubtitleLanguages": ["eng"],
  "FileSize": 2147483648
}'

# Check if curl and jq are installed
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed. Please install curl to use this script.${NC}"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq is not installed. JSON formatting will be disabled.${NC}"
    echo -e "${YELLOW}To install jq: sudo apt-get install jq (Debian/Ubuntu) or brew install jq (macOS)${NC}"
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Jellyfin Telegram Notifier - Webhook Test${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Send webhook tests based on item type
case $ITEM_TYPE in
    movie)
        send_webhook "Movie" "$movie_payload"
        ;;
    season)
        send_webhook "Season" "$season_payload"
        ;;
    episode)
        send_webhook "Episode" "$episode_payload"
        ;;
    all)
        send_webhook "Movie" "$movie_payload"
        send_webhook "Season" "$season_payload"
        send_webhook "Episode" "$episode_payload"
        ;;
    *)
        echo -e "${RED}Error: Invalid item type '$ITEM_TYPE'${NC}"
        echo "Valid types: movie, season, episode, all"
        exit 1
        ;;
esac

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Webhook tests completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Check your Telegram chat to verify notifications were received.${NC}"
echo ""
