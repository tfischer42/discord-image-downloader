# Discord Image Downloader

A Python command-line tool for downloading images from Discord channels using the Discord API. Perfect for archiving photos shared in Discord conversations without clicking through each one individually.

## Features

- Download all images from Discord channel messages
- Support for multiple image formats (PNG, JPG, JPEG, GIF, WEBP, BMP)
- Filter messages using Discord's query parameters:
  - `--before`: Get messages before a specific message ID
  - `--after`: Get messages after a specific message ID
  - `--around`: Get messages around a specific message ID
- Configurable message limit (1-100 messages per request)
- Automatic organization with unique filenames (prevents overwrites)
- Progress feedback during downloads
- Secure token storage using environment variables

## Installation

1. **Clone the repository**
```bash
   git clone https://github.com/yourusername/discord-image-downloader.git
   cd discord-image-downloader
```

2. **Create and activate a virtual environment**
   
   On Windows:
```bash
   python -m venv venv
   venv\Scripts\activate
```
   
   On Mac/Linux:
```bash
   python -m venv venv
   source venv/bin/activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

4. **Set up your Discord token**
   
   Create a `.env` file in the project root:
```
   DISCORD_TOKEN=your_token_here
```
   (See "Getting Your Discord Token" below for instructions)

## Usage

Basic usage:
```bash
python download_images.py CHANNEL_ID
```

With options:
```bash
# Download up to 50 messages
python download_images.py CHANNEL_ID --limit 50

# Get messages before a specific message ID
python download_images.py CHANNEL_ID --before 123456789012345678

# Get messages after a specific message ID
python download_images.py CHANNEL_ID --after 123456789012345678

# Get messages around a specific message ID
python download_images.py CHANNEL_ID --around 123456789012345678
```

**Examples:**
```bash
# Download images from the most recent 100 messages
python download_images.py 987654321098765432

# Download images from the most recent 25 messages
python download_images.py 987654321098765432 --limit 25

# Download images from messages before a specific point
python download_images.py 987654321098765432 --before 111222333444555666
```

Downloaded images will be saved to the `./downloads` folder with filenames in the format `{message_id}_{original_filename}`.

## Getting Your Discord Token

**⚠️ Important: Your Discord token is like a password. Never share it with anyone!**

1. Open Discord in your web browser (Chrome, Firefox, etc.) and log in
2. Press `F12` to open Developer Tools
3. Click on the **Network** tab
4. Type any message in any Discord channel (this triggers a network request)
5. Look for a request in the Network tab and click on it
6. In the **Headers** section, scroll down to **Request Headers**
7. Find the `authorization` header - this is your token
8. Copy the token value and paste it into your `.env` file

**Security tips:**
- Never commit your `.env` file to Git (it's already in `.gitignore`)
- Don't share your token in screenshots or error messages
- If your token is ever compromised, change your Discord password immediately to invalidate it

## Finding Channel IDs

1. Enable Developer Mode in Discord:
   - Open Discord Settings (gear icon)
   - Go to **Advanced** (under "App Settings")
   - Enable **Developer Mode**

2. Get a Channel ID:
   - Right-click on any channel
   - Select **Copy Channel ID**
   - Use this ID when running the script

## Security Warning

This tool uses your personal Discord token to authenticate API requests. Please note:

- **Keep your token private** - treat it like a password
- **Don't run untrusted code** - only use this tool from the official repository
- **The `.env` file is gitignored** - but always double-check before committing
- **Automating user accounts** may be against Discord's Terms of Service - use at your own risk
- If you suspect your token has been compromised, change your Discord password immediately

This tool is intended for personal use to download your own data from channels you have access to.

## Future Plans

### Near-term improvements
- **Pagination support** - Automatically fetch more than 100 messages by chaining multiple API requests
- **Progress bars** - Visual feedback during large downloads
- **Batch processing** - Download from multiple channels in one run
- **Rate limit handling** - Smarter throttling to avoid Discord API limits
- **Download resume** - Pick up where you left off if interrupted

### UI Development (Next Major Focus)
We're planning to evolve this project beyond a CLI tool with improved user experience:

- **Web Application** - Browser-based interface for easier token/channel ID management
  - Visual channel browser (no more copying IDs manually)
  - OAuth integration for secure authentication (no token copying required)
  - Preview images before downloading
  - Batch selection and filtering options

- **Discord Bot** ✅ **NOW AVAILABLE!** - Alternative deployment as a bot users can add to their servers
  - Slash commands for downloading images
  - Direct integration within Discord
  - No need for users to manage tokens manually

## Discord Bot

The project now includes a Discord bot (`bot.py`) that provides the same image downloading functionality through slash commands!

### Bot Setup

1. **Create a Discord Bot**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" and give it a name
   - Go to the "Bot" section and click "Add Bot"
   - Under "Privileged Gateway Intents", enable:
     - Message Content Intent
     - Server Members Intent (optional)
   - Copy your bot token

2. **Add BOT_TOKEN to .env**:
   ```
   BOT_TOKEN=your_bot_token_here
   ```

3. **Invite the bot to your server**:
   - Go to the "OAuth2" → "URL Generator" section
   - Select scopes: `bot` and `applications.commands`
   - Select bot permissions:
     - Read Messages/View Channels
     - Read Message History
     - Send Messages
     - Attach Files
   - Copy the generated URL and open it in your browser
   - Select your server and authorize the bot

4. **Run the bot**:
   ```bash
   python bot.py
   ```

### Bot Commands

The bot provides a `/download` slash command with the following options:

- `channel` (required): The channel to download images from
- `limit` (optional): Number of messages to fetch (1-100, default: 50)
- `before` (optional): Message ID to fetch messages before
- `after` (optional): Message ID to fetch messages after
- `around` (optional): Message ID to fetch messages around
- `fetch_all` (optional): Fetch ALL messages using pagination

**Examples:**
```
/download channel:#photos limit:50
/download channel:#memes fetch_all:True
/download channel:#archive before:123456789012345678 limit:100
```

**Bot Features:**
- ✅ Downloads images directly to Discord (no need to access files locally)
- ✅ Automatically creates zip files for large collections (>10 images)
- ✅ Real-time progress updates
- ✅ Built-in permission checking
- ✅ User-friendly error messages
- ✅ Supports all query parameters (before/after/around)
- ✅ Full pagination support with `fetch_all` option