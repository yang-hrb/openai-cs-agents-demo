#!/usr/bin/env python3
"""
Apple Podcast Episode Downloader
Downloads podcast episodes to MP3 format
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path


def download_podcast(url: str, output_dir: str = ".", format: str = "mp3") -> bool:
    """
    Download a podcast episode from Apple Podcasts or other sources to MP3.

    Args:
        url: URL of the podcast episode (Apple Podcasts, RSS feed, etc.)
        output_dir: Directory to save the downloaded file
        format: Output format (default: mp3)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Check if yt-dlp is installed
        try:
            subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: yt-dlp is not installed.")
            print("Please install it using: pip install yt-dlp")
            return False

        # Download podcast episode using yt-dlp
        print(f"Downloading podcast from: {url}")
        print(f"Output directory: {output_dir}")
        print(f"Format: {format}")

        # yt-dlp command to download and convert to mp3
        command = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", format,  # Convert to specified format
            "--audio-quality", "0",  # Best quality
            "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),  # Output template
            url
        ]

        # Run the download command
        result = subprocess.run(
            command,
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"\n✓ Successfully downloaded podcast to {output_dir}")
            return True
        else:
            print(f"\n✗ Failed to download podcast (exit code: {result.returncode})")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Download Apple Podcast episodes to MP3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from Apple Podcasts URL
  python podcast_downloader.py --apple_podcast "https://podcasts.apple.com/us/podcast/..."

  # Download to specific directory
  python podcast_downloader.py --apple_podcast "URL" --output ./podcasts

  # Download as different format
  python podcast_downloader.py --apple_podcast "URL" --format m4a
        """
    )

    parser.add_argument(
        "--apple_podcast",
        type=str,
        required=True,
        help="URL of the Apple Podcast episode to download"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./podcasts",
        help="Output directory for downloaded files (default: ./podcasts)"
    )

    parser.add_argument(
        "--format",
        type=str,
        default="mp3",
        choices=["mp3", "m4a", "wav", "flac", "opus"],
        help="Audio format for the output file (default: mp3)"
    )

    args = parser.parse_args()

    # Download the podcast
    success = download_podcast(
        url=args.apple_podcast,
        output_dir=args.output,
        format=args.format
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
