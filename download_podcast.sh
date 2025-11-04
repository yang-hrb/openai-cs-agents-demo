#!/bin/bash
###############################################################################
# Apple Podcast Episode Downloader Shell Script
#
# This script provides an easy way to download Apple Podcast episodes to MP3
#
# Usage:
#   ./download_podcast.sh <podcast_url> [output_dir] [format]
#
# Examples:
#   ./download_podcast.sh "https://podcasts.apple.com/us/podcast/..."
#   ./download_podcast.sh "https://podcasts.apple.com/us/podcast/..." ./my_podcasts
#   ./download_podcast.sh "https://podcasts.apple.com/us/podcast/..." ./my_podcasts m4a
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/python-backend"

# Default values
OUTPUT_DIR="./podcasts"
FORMAT="mp3"

# Check if URL is provided
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: Podcast URL is required${NC}"
    echo ""
    echo "Usage: $0 <podcast_url> [output_dir] [format]"
    echo ""
    echo "Examples:"
    echo "  $0 'https://podcasts.apple.com/us/podcast/...'"
    echo "  $0 'https://podcasts.apple.com/us/podcast/...' ./my_podcasts"
    echo "  $0 'https://podcasts.apple.com/us/podcast/...' ./my_podcasts m4a"
    exit 1
fi

PODCAST_URL="$1"

# Override output directory if provided
if [ -n "$2" ]; then
    OUTPUT_DIR="$2"
fi

# Override format if provided
if [ -n "$3" ]; then
    FORMAT="$3"
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    echo "Please install Python 3 to use this script"
    exit 1
fi

# Check if virtual environment exists, create if not
VENV_DIR="$BACKEND_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if requirements are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! python3 -c "import yt_dlp" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q -r "$BACKEND_DIR/requirements.txt"
fi

# Run the podcast downloader
echo -e "${GREEN}Starting podcast download...${NC}"
echo ""
python3 "$BACKEND_DIR/podcast_downloader.py" \
    --apple_podcast "$PODCAST_URL" \
    --output "$OUTPUT_DIR" \
    --format "$FORMAT"

EXIT_CODE=$?

# Deactivate virtual environment
deactivate

# Print final status
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Podcast download completed successfully!${NC}"
    echo -e "Files saved to: ${GREEN}$OUTPUT_DIR${NC}"
else
    echo -e "${RED}✗ Podcast download failed${NC}"
fi

exit $EXIT_CODE
