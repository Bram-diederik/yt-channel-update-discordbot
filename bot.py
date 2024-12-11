import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
import asyncio
import json
import logging
import re
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# Configure logging
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHECK_INTERVAL = float(os.getenv("CHECK_INTERVAL", 3600))
ALLOWED_GUILD_ID = os.getenv("ALLOWED_GUILD_ID")  
DEBUG_LOGGING = os.getenv("DEBUG_LOGGING", "1") == "1"
logging_level = logging.DEBUG if DEBUG_LOGGING else logging.INFO
logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')



data = {
    "channels": {},
    "last_video": {},
    "post_channels": {}
}

@bot.command(name="add_channel")
@commands.has_permissions(manage_guild=True)
async def add_channel(ctx, youtube_channel_url, *hashtags):
    guild_id = str(ctx.guild.id)
    logging.debug(f"Adding YouTube channel URL: {youtube_channel_url} to guild ID: {guild_id} with hashtags: {hashtags}")
    
    channel_id = get_channel_id_from_url(youtube_channel_url)
    if not channel_id:
        await ctx.send("Invalid YouTube URL. Make sure you provide a channel.")
        return

    if guild_id not in data["channels"]:
        data["channels"][guild_id] = {}

    if channel_id not in data["channels"][guild_id]:
        data["channels"][guild_id][channel_id] = list(hashtags)
        await ctx.send(f"Added YouTube channel: {youtube_channel_url} with hashtags: {', '.join(hashtags) if hashtags else 'None'}")
        save_data()
    else:
        await ctx.send("YouTube channel already added.")

def get_matching_hashtags(channel_id, description):
    """Return matching hashtags for a given channel based on description."""
    for guild_channels in data["channels"].values():
        if channel_id in guild_channels:
            channel_hashtags = guild_channels[channel_id]
            if not channel_hashtags:  # No hashtags = post everything
                return True
            return any(hashtag.lower() in description for hashtag in channel_hashtags)
    return False

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_new_videos():
    """Periodically check for new YouTube videos and post updates."""
    logging.info("Running video check task...")
    for admin_guild_id, youtube_channel_ids in data["channels"].items():
        for youtube_channel_id, hashtags in youtube_channel_ids.items():
            logging.warning(f"Processing YouTube channel ID: {youtube_channel_id}.")
            video = get_latest_video(youtube_channel_id)
            if not video:
                continue

            # Check if the video is already posted
            if video["id"] == data["last_video"].get(youtube_channel_id):
                continue

            # Check hashtags if any are defined
            description = video.get("description", "").lower()
            if get_matching_hashtags(youtube_channel_id, description):
                logging.info(f"New video detected: {video['title']}")
                data["last_video"][youtube_channel_id] = video["id"]
                save_data()

                # Notify all guilds with a configured post channel
                for guild_id, post_channel_id in data["post_channels"].items():
                    channel = bot.get_channel(int(post_channel_id))
                    if channel:
                        await channel.send(f"New video: **{video['title']}**\n{video['url']}")
                        logging.debug(f"Posted new video to channel ID: {post_channel_id}")
                    else:
                        logging.warning(f"Discord channel ID {post_channel_id} not found.")
            else:
                logging.info(f"No matching hashtags for video: {video['title']}")


def save_data():
    with open("bot_data.json", "w") as file:
        json.dump(data, file)
    logging.debug("Data saved to file.")

def load_data():
    global data
    try:
        with open("bot_data.json", "r") as file:
            data.update(json.load(file))
        logging.debug("Data loaded from file.")
    except FileNotFoundError:
        logging.warning("Data file not found; starting with empty data.")

def get_channel_id_from_url(url):

    """Extracts the channel ID from a YouTube URL.

    Args:
        url (str): The YouTube URL to extract the channel ID from.

    Returns:
        str: The extracted channel ID, or None if the URL is invalid.
    """

    # Improved regular expression for robust channel ID extraction:
    pattern = r"(?:https?://)?(?:www\.)?youtube\.com/(?:(?:channel)/([^/?]+))"
    match = re.search(pattern, url)

    if match:
        return match.group(1)  # Extract the first capturing group (channel ID)
    else:
        return None

def get_latest_video(channel_id):
    """Fetch the latest video from a YouTube channel."""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet", channelId=channel_id, maxResults=1, order="date", type="video"
    )
    logging.debug(f"Fetching latest video for channel ID: {channel_id}")
    try:
        response = request.execute()
        if not response["items"]:
            logging.info(f"No videos found for channel ID: {channel_id}")
            return None
        video = response["items"][0]
        video_id = video["id"]["videoId"]
        logging.debug(f"Latest video fetched: {video['snippet']['title']}")

        # Fetch detailed video info to get the description
        video_details_request = youtube.videos().list(
            part="snippet", id=video_id
        )
        video_details_response = video_details_request.execute()
        if not video_details_response["items"]:
            logging.info(f"Video not found for ID: {video_id}")
            return None
        
        video_details = video_details_response["items"][0]["snippet"]
        logging.debug(f"Video details: {video_details}")

        # Build the video data
        return {
            "id": video_id,
            "title": video_details["title"],
            "description": video_details.get("description", ""),
            "url": f"https://youtu.be/{video_id}",
        }
    except Exception as e:
        logging.error(f"Error fetching latest video: {e}")
        return None




@bot.event
async def on_ready():
    logging.info(f"Bot logged in as {bot.user}")
    logging.info(f"Admin guild ID: {ALLOWED_GUILD_ID}")
    load_data()
    for guild in bot.guilds:
        logging.info(f"Currently in guild: {guild.name} (ID: {guild.id})")
    
    if not check_new_videos.is_running():
        check_new_videos.start()

@bot.event
async def on_guild_join(guild):
    if str(guild.id) != ALLOWED_GUILD_ID:
        logging.warning(f"Bot invited to unauthorized guild: {guild.name}")
        if guild.system_channel:
            await guild.system_channel.send(
                "This bot is restricted by commands on this channel"
            )



@bot.command(name="set_post_channel")
@commands.has_permissions(manage_guild=True)
async def add_post_channel(ctx, channel: discord.TextChannel):
    guild_id = str(ctx.guild.id)
    data["post_channels"][guild_id] = channel.id
    await ctx.send(f"Set channel to post youtube videos on to: {channel.mention}")
    save_data()

@bot.command(name="delete_channel")
@commands.has_permissions(manage_guild=True)
async def delete_channel(ctx, youtube_channel_url):
    guild_id = str(ctx.guild.id)
    channel_id = get_channel_id_from_url(youtube_channel_url)

    if guild_id in data["channels"] and channel_id in data["channels"][guild_id]:
        data["channels"][guild_id].remove(channel_id)
        await ctx.send(f"Removed YouTube channel: {youtube_channel_url}")
        save_data()
    else:
        await ctx.send("YouTube channel not found.")


@bot.command(name="list_channels")
@commands.has_permissions(manage_guild=True)
async def list_channels(ctx):
    guild_id = str(ctx.guild.id)
    
    if guild_id in data["channels"] and data["channels"][guild_id]:
        channels_info = []
        for channel_id, hashtags in data["channels"][guild_id].items():
            hashtag_list = ", ".join(hashtags) if hashtags else "No hashtags"
            channels_info.append(f"Channel ID: {channel_id}\nHashtags: {hashtag_list}")
        
        await ctx.send("Tracked YouTube channels:\n" + "\n\n".join(channels_info))
    else:
        await ctx.send("No YouTube channels are currently tracked for this server.")


# Run the bot
bot.run(DISCORD_TOKEN)

