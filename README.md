YouTube Hashtag Bot

This bot is designed to track YouTube channels and notify Discord servers about new videos. It can filter videos by hashtags or post all updates depending on the configuration.
Features

    Add and remove YouTube channels for tracking.
    Set specific hashtags for filtering videos.
    Automatically post updates for new videos to designated channels.
    Admin-only commands for server management.

Commands
!add_channel <url> [hashtags...]

Adds a YouTube channel for tracking in the current Discord server. Optionally, you can provide one or more hashtags for filtering videos.

    Parameters:
        url: The URL of the YouTube channel (e.g., https://www.youtube.com/channel/UC123...).
        hashtags... (optional): Space-separated hashtags to filter videos by their description (e.g., #gaming #tutorial).

    Example:
        !add_channel https://www.youtube.com/channel/UC12345abc #gaming #tutorial
        !add_channel https://www.youtube.com/channel/UC67890xyz

    Note: If no hashtags are specified, all videos from the channel will be posted.

!delete_channel <url>

Removes a YouTube channel from the tracking list for the current Discord server.

    Parameters:
        url: The URL of the YouTube channel to remove.

    Example:
        !delete_channel https://www.youtube.com/channel/UC12345abc

!list_channels

Lists all YouTube channels currently being tracked in the server, along with their associated hashtags.

    Example:
        Output:

        Tracked YouTube channels:
        Channel ID: UC12345abc
        Hashtags: #gaming, #tutorial

        Channel ID: UC67890xyz
        Hashtags: No hashtags

!set_post_channel <channel>

Sets the specified Discord text channel as the destination for posting updates about new videos.

    Parameters:
        channel: Mention or ID of the text channel.

    Example:
        !add_post_channel #youtube-updates

Setup and Usage

    Invite the bot: Invite the bot to your server with the necessary permissions.
    Add YouTube channels: Use the !add_channel command to start tracking channels.
    Set a post channel: Use !add_post_channel to specify where the bot should send updates.
    Optional: Use hashtags to filter videos by description.

Permissions

The bot requires the following permissions:

    Manage Messages: For tracking updates.
    Send Messages: To notify about new videos.
    Read Message History: To interact in text channels.

Only users with the Manage Server permission can use the bot's commands.
Notes

    The bot runs on an interval to check for new videos (default: 1 hour).
    Hashtag filtering is case-insensitive.

Enjoy using the YouTube Hashtag Bot! 🎥
