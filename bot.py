"""
Discord Image Downloader Bot
A Discord bot that downloads images from channels using slash commands.
"""

import os
import io
import zipfile
import tempfile
import asyncio
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


class ImageDownloaderBot(commands.Bot):
    """Discord bot for downloading images from channels."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Called when the bot is starting up."""
        await self.tree.sync()
        print("✓ Slash commands synced")

    async def on_ready(self):
        """Called when the bot is ready."""
        print(f"✓ Bot logged in as {self.user}")
        print(f"✓ Connected to {len(self.guilds)} guild(s)")
        print("=" * 50)


# Initialize bot
bot = ImageDownloaderBot()


@bot.tree.command(name="download", description="Download images from a Discord channel")
@app_commands.describe(
    channel="The channel to download images from",
    limit="Number of messages to fetch (1-100, default: 50)",
    before="Message ID to fetch messages before",
    after="Message ID to fetch messages after",
    around="Message ID to fetch messages around",
    fetch_all="Fetch ALL messages using pagination (ignores limit)",
)
async def download_images(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    limit: Optional[int] = 50,
    before: Optional[str] = None,
    after: Optional[str] = None,
    around: Optional[str] = None,
    fetch_all: Optional[bool] = False,
):
    """
    Download images from a Discord channel.

    Args:
        interaction: The Discord interaction
        channel: The channel to download from
        limit: Number of messages to fetch
        before: Message ID to fetch before
        after: Message ID to fetch after
        around: Message ID to fetch around
        fetch_all: Whether to fetch all messages
    """
    # Defer the response since this might take a while
    await interaction.response.defer(thinking=True)

    try:
        # Validate mutual exclusivity
        query_params = [before, after, around]
        query_params_set = [p for p in query_params if p is not None]

        if len(query_params_set) > 1:
            await interaction.followup.send(
                "❌ Error: `before`, `after`, and `around` are mutually exclusive. "
                "Please use only one at a time.",
                ephemeral=True,
            )
            return

        # Validate fetch_all compatibility
        if fetch_all and len(query_params_set) > 0:
            await interaction.followup.send(
                "❌ Error: `fetch_all` cannot be used with `before`, `after`, or `around`. "
                "The fetch_all option automatically paginates through all messages.",
                ephemeral=True,
            )
            return

        # Validate limit
        if limit < 1 or limit > 100:
            await interaction.followup.send(
                "❌ Error: `limit` must be between 1 and 100.",
                ephemeral=True,
            )
            return

        # Check bot permissions
        if not channel.permissions_for(interaction.guild.me).read_message_history:
            await interaction.followup.send(
                f"❌ Error: I don't have permission to read message history in {channel.mention}.",
                ephemeral=True,
            )
            return

        # Send initial status message
        await interaction.followup.send(
            f"🔄 Starting download from {channel.mention}...\n"
            f"Mode: {'Fetch all messages' if fetch_all else f'Fetch up to {limit} messages'}"
        )

        # Fetch messages
        images = []
        total_messages = 0

        if fetch_all:
            # Fetch all messages with pagination
            status_msg = await interaction.followup.send(
                "📥 Fetching messages (batch 1)..."
            )
            batch_count = 0
            before_id = None

            while True:
                batch_count += 1

                # Fetch batch
                batch = []
                async for message in channel.history(
                    limit=100,
                    before=discord.Object(id=int(before_id)) if before_id else None,
                ):
                    batch.append(message)

                if not batch:
                    break

                total_messages += len(batch)

                # Extract images from batch
                for message in batch:
                    for attachment in message.attachments:
                        if any(
                            attachment.filename.lower().endswith(ext)
                            for ext in [
                                ".png",
                                ".jpg",
                                ".jpeg",
                                ".gif",
                                ".webp",
                                ".bmp",
                            ]
                        ):
                            images.append(
                                {
                                    "url": attachment.url,
                                    "filename": f"{message.id}_{attachment.filename}",
                                    "attachment": attachment,
                                }
                            )

                # Update status
                await status_msg.edit(
                    content=f"📥 Batch {batch_count}: {len(batch)} messages | "
                    f"Total: {total_messages} messages, {len(images)} images found"
                )

                # Check if we've reached the end
                if len(batch) < 100:
                    break

                # Get the oldest message ID for next iteration
                before_id = str(batch[-1].id)

                # Rate limiting
                await asyncio.sleep(0.5)

        else:
            # Fetch single batch
            before_obj = discord.Object(id=int(before)) if before else None
            after_obj = discord.Object(id=int(after)) if after else None
            around_obj = discord.Object(id=int(around)) if around else None

            async for message in channel.history(
                limit=limit, before=before_obj, after=after_obj, around=around_obj
            ):
                total_messages += 1
                for attachment in message.attachments:
                    if any(
                        attachment.filename.lower().endswith(ext)
                        for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]
                    ):
                        images.append(
                            {
                                "url": attachment.url,
                                "filename": f"{message.id}_{attachment.filename}",
                                "attachment": attachment,
                            }
                        )

        # Check if any images were found
        if not images:
            await interaction.followup.send(
                f"✅ Scanned {total_messages} messages, but no images were found."
            )
            return

        # Download and send images
        await interaction.followup.send(
            f"📊 Found {len(images)} image(s) in {total_messages} messages. Downloading..."
        )

        # If there are many images, we'll need to zip them
        if len(images) <= 10:
            # Send images directly (Discord limit is 10 files per message)
            files_to_send = []
            for idx, img in enumerate(images, 1):
                try:
                    # Download the image
                    image_data = await img["attachment"].read()
                    files_to_send.append(
                        discord.File(io.BytesIO(image_data), filename=img["filename"])
                    )

                    if idx % 5 == 0:
                        await interaction.followup.send(
                            f"⬇️ Downloaded {idx}/{len(images)} images..."
                        )
                except Exception as e:
                    await interaction.followup.send(
                        f"⚠️ Failed to download {img['filename']}: {str(e)}"
                    )

            # Send all images
            if files_to_send:
                await interaction.followup.send(
                    f"✅ Downloaded {len(files_to_send)} image(s)!", files=files_to_send
                )
        else:
            # Create a zip file
            await interaction.followup.send(
                f"📦 Creating zip file with {len(images)} images (too many to send individually)..."
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / f"images_{channel.name}_{channel.id}.zip"

                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for idx, img in enumerate(images, 1):
                        try:
                            # Download the image
                            image_data = await img["attachment"].read()

                            # Add to zip
                            zipf.writestr(img["filename"], image_data)

                            # Progress updates every 20 images
                            if idx % 20 == 0:
                                await interaction.followup.send(
                                    f"⬇️ Downloaded {idx}/{len(images)} images..."
                                )
                        except Exception as e:
                            await interaction.followup.send(
                                f"⚠️ Failed to download {img['filename']}: {str(e)}"
                            )

                # Check file size (Discord limit is 25MB for normal servers, 100MB for nitro)
                zip_size_mb = zip_path.stat().st_size / (1024 * 1024)

                if zip_size_mb > 25:
                    await interaction.followup.send(
                        f"⚠️ Warning: Zip file is {zip_size_mb:.1f}MB. "
                        f"Discord has a 25MB limit (100MB with Nitro)."
                    )

                # Send the zip file
                with open(zip_path, "rb") as f:
                    await interaction.followup.send(
                        f"✅ Downloaded {len(images)} images!",
                        file=discord.File(f, filename=zip_path.name),
                    )

    except discord.Forbidden:
        await interaction.followup.send(
            f"❌ Error: I don't have permission to access {channel.mention}.",
            ephemeral=True,
        )
    except discord.HTTPException as e:
        await interaction.followup.send(
            f"❌ Discord API error: {str(e)}", ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Unexpected error: {str(e)}", ephemeral=True
        )
        raise  # Re-raise for debugging


def main():
    """Main entry point for the bot."""
    # Load environment variables
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        print("❌ Error: BOT_TOKEN not found in .env file")
        print("  Please add your Discord bot token to the .env file:")
        print("  BOT_TOKEN=your_bot_token_here")
        return

    print("Discord Image Downloader Bot")
    print("=" * 50)
    print("Starting bot...")

    try:
        bot.run(bot_token)
    except discord.LoginFailure:
        print("❌ Error: Invalid bot token")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")


if __name__ == "__main__":
    main()
