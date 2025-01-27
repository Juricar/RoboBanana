import logging
from discord import Client, Intents, Message

from server.blueprints.chat import publish_chat

from config import Config
import re

LOG = logging.getLogger(__name__)

GUILD_ID = int(Config.CONFIG["Predictions"]["GuildID"])

CUSTOM_EMOJI_PATTERN = re.compile(r"(<a?:[a-zA-Z0-9]+:([0-9]+)>)")
USER_PATTERN = re.compile(r"(<@([0-9]+)>)")
CHANNEL_PATTERN = re.compile(r"(<#([0-9]+)>)")


class ServerBot(Client):
    def __init__(self):
        intents = Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True

        super().__init__(intents=intents)

    async def on_ready(self):
        LOG.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: Message):
        stream = False
        test = False
        if message.channel.id == 915336728707989537:
            test = True

        if message.channel.id == 1037040541017309225:
            stream = True

        # Valorant Discussion Channel (high volume good for testing)
        if stream or test:
            should_send, emoji_content = self.find_emojis(message.content)
            if not should_send:
                return
            to_send = {
                "content": message.content,
                "displayName": (
                    message.author.nick
                    if message.author.nick is not None
                    else message.author.display_name
                ),
                "roles": [
                    {
                        "colorR": r.color.r,
                        "colorG": r.color.g,
                        "colorB": r.color.b,
                        "icon": None if r.icon is None else r.icon.url,
                        "id": r.id,
                        "name": r.name,
                    }
                    for r in message.author.roles
                ],
                "stickers": [{"url": s.url} for s in message.stickers],
                "emojis": emoji_content,
                "mentions": self.find_users(message.content) + self.find_channels(
                    message.content
                ),
            }
            LOG.debug(to_send)
            await publish_chat(to_send, stream)

    def find_emojis(self, content: str):
        stream_content = []
        emoji_matches = CUSTOM_EMOJI_PATTERN.findall(content)
        for emoji_text, emoji_id in emoji_matches:
            emoji = self.get_emoji(int(emoji_id))
            if emoji is None:
                LOG.warn(f"Could not find custom emoji {emoji_text}")
                return False, []
            stream_content.append({"emoji_text": emoji_text, "emoji_url": emoji.url})
        return True, stream_content

    def find_users(self, content: str):
        stream_content = []
        user_matches = USER_PATTERN.findall(content)
        for user_text, user_id in user_matches:
            member = self.get_guild(GUILD_ID).get_member(int(user_id))
            if member is None:
                LOG.warn(f"Unable to find user {user_id=}")
                continue
            stream_content.append(
                {
                    "mention_text": user_text,
                    "display_name": f"@{member.display_name}",
                }
            )
        return stream_content

    def find_channels(self, content: str):
        LOG.info("HERE")
        stream_content = []
        channel_matches = CHANNEL_PATTERN.findall(content)
        for channel_text, channel_id in channel_matches:
            channel = self.get_guild(GUILD_ID).get_channel(int(channel_id))
            if channel is None:
                LOG.warn(f"Unable to find channel {channel_id=}")
                continue
            stream_content.append(
                {"mention_text": channel_text, "display_name": f"# {channel.name}"}
            )
        return stream_content


async def start_discord_client(client: Client):
    async with client:
        await client.start(Config.CONFIG["Discord"]["Token"])


DISCORD_CLIENT = ServerBot()
