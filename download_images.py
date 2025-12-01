"""
Discord Image Downloader
Downloads all images from Discord channel messages using the Discord API.
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse


class DiscordImageDownloader:
    """Handles downloading images from Discord channels."""

    def __init__(self, token: str):
        """
        Initialize the downloader with Discord token.

        Args:
            token: Discord user token for authentication
        """
        self.token = token
        self.headers = {"Authorization": token}
        self.base_url = "https://discord.com/api/v9"
        self.downloads_dir = Path("./downloads")

    def create_downloads_directory(self):
        """Create the downloads directory if it doesn't exist."""
        self.downloads_dir.mkdir(exist_ok=True)
        print(f"✓ Downloads directory ready: {self.downloads_dir.absolute()}")

    def fetch_messages(
        self,
        channel_id: str,
        limit: int = 100,
        before: str = None,
        after: str = None,
        around: str = None,
    ) -> list:
        """
        Fetch messages from a Discord channel.

        Args:
            channel_id: The Discord channel ID to fetch messages from
            limit: Maximum number of messages to fetch (default: 100, max: 100)
            before: Get messages before this message ID
            after: Get messages after this message ID
            around: Get messages around this message ID

        Returns:
            List of message objects

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        url = f"{self.base_url}/channels/{channel_id}/messages"
        params = {"limit": min(limit, 100)}  # Discord API max is 100 per request

        # Add optional query parameters
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if around:
            params["around"] = around

        # Build query description for user feedback
        query_desc = f"Fetching up to {limit} messages from channel {channel_id}"
        if before:
            query_desc += f" (before message {before})"
        elif after:
            query_desc += f" (after message {after})"
        elif around:
            query_desc += f" (around message {around})"
        query_desc += "..."
        print(query_desc)

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            messages = response.json()
            print(f"✓ Retrieved {len(messages)} messages")
            return messages

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print("✗ Authentication failed. Please check your DISCORD_TOKEN.")
            elif response.status_code == 403:
                print(
                    "✗ Access forbidden. You may not have permission to view this channel."
                )
            elif response.status_code == 404:
                print("✗ Channel not found. Please check the channel ID.")
            else:
                print(f"✗ HTTP error occurred: {e}")
            raise

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching messages: {e}")
            raise

    def get_image_attachments(self, messages: list) -> list:
        """
        Extract image attachments from messages.

        Args:
            messages: List of Discord message objects

        Returns:
            List of tuples containing (image_url, filename, message_id)
        """
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
        images = []

        for message in messages:
            if "attachments" in message and message["attachments"]:
                for attachment in message["attachments"]:
                    # Check if the attachment is an image
                    url = attachment.get("url", "")
                    filename = attachment.get("filename", "")

                    # Check file extension
                    file_ext = Path(filename).suffix.lower()
                    if file_ext in image_extensions:
                        # Create a unique filename using message ID
                        unique_filename = f"{message['id']}_{filename}"
                        images.append((url, unique_filename, message["id"]))

        return images

    def download_image(self, url: str, filename: str) -> bool:
        """
        Download a single image from URL.

        Args:
            url: Image URL to download from
            filename: Filename to save the image as

        Returns:
            True if download successful, False otherwise
        """
        filepath = self.downloads_dir / filename

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Failed to download {filename}: {e}")
            return False

    def download_images_from_channel(
        self,
        channel_id: str,
        limit: int = 100,
        before: str = None,
        after: str = None,
        around: str = None,
    ):
        """
        Main method to download all images from a channel.

        Args:
            channel_id: Discord channel ID
            limit: Maximum number of messages to fetch
            before: Get messages before this message ID
            after: Get messages after this message ID
            around: Get messages around this message ID
        """
        # Create downloads directory
        self.create_downloads_directory()

        # Fetch messages
        try:
            messages = self.fetch_messages(channel_id, limit, before, after, around)
        except requests.exceptions.RequestException:
            print("\n✗ Failed to fetch messages. Exiting.")
            return

        # Extract image attachments
        images = self.get_image_attachments(messages)

        if not images:
            print("\n✓ No images found in the fetched messages.")
            return

        print(f"\nFound {len(images)} image(s) to download...")
        print("-" * 50)

        # Download images
        success_count = 0
        for idx, (url, filename, message_id) in enumerate(images, 1):
            print(f"[{idx}/{len(images)}] Downloading {filename}...", end=" ")

            if self.download_image(url, filename):
                print("✓")
                success_count += 1
            else:
                print("✗")

        # Summary
        print("-" * 50)
        print(f"\n✓ Download complete!")
        print(f"  Successfully downloaded: {success_count}/{len(images)} images")
        print(f"  Location: {self.downloads_dir.absolute()}")


def main():
    """Main entry point for the script."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Download images from Discord channel messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_images.py 123456789012345678
  python download_images.py 123456789012345678 --limit 50
  python download_images.py 123456789012345678 --before 987654321098765432
  python download_images.py 123456789012345678 --after 111222333444555666
  python download_images.py 123456789012345678 --around 555666777888999000 --limit 50
        """,
    )

    parser.add_argument(
        "channel_id", type=str, help="Discord channel ID to download images from"
    )

    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=100,
        help="Maximum number of messages to fetch (default: 100, max: 100)",
    )

    parser.add_argument(
        "--before",
        type=str,
        metavar="MESSAGE_ID",
        help="Get messages before this message ID (useful for pagination)",
    )

    parser.add_argument(
        "--after",
        type=str,
        metavar="MESSAGE_ID",
        help="Get messages after this message ID (useful for getting newer messages)",
    )

    parser.add_argument(
        "--around",
        type=str,
        metavar="MESSAGE_ID",
        help="Get messages around this message ID (gets context before and after)",
    )

    args = parser.parse_args()

    # Validate mutual exclusivity of before/after/around parameters
    query_params = [args.before, args.after, args.around]
    query_params_set = [p for p in query_params if p is not None]

    if len(query_params_set) > 1:
        print("✗ Error: --before, --after, and --around are mutually exclusive")
        print("  Please use only one of these parameters at a time.")
        sys.exit(1)

    # Load environment variables
    load_dotenv()
    discord_token = os.getenv("DISCORD_TOKEN")

    if not discord_token:
        print("✗ Error: DISCORD_TOKEN not found in .env file")
        print("  Please create a .env file with your Discord token:")
        print("  DISCORD_TOKEN=your_token_here")
        sys.exit(1)

    # Validate limit
    if args.limit < 1:
        print("✗ Error: Limit must be at least 1")
        sys.exit(1)

    if args.limit > 100:
        print(
            "⚠ Warning: Discord API limits to 100 messages per request. Using limit of 100."
        )
        args.limit = 100

    # Run downloader
    print("Discord Image Downloader")
    print("=" * 50)

    downloader = DiscordImageDownloader(discord_token)
    downloader.download_images_from_channel(
        args.channel_id, args.limit, args.before, args.after, args.around
    )


if __name__ == "__main__":
    main()
