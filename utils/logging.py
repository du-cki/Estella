import logging

from io import BytesIO
from datetime import datetime

from discord import SyncWebhook, Embed, File
from discord.utils import _ColourFormatter  # pyright: ignore[reportPrivateUsage]

from .functions import to_cb

from config import LOG_FUNNEL_WEBHOOK


CODEBLOCK_LEN = len("```py\n\n```")
MESSAGE_LIMIT = 2000
EMBED_LIMIT = 4096


class DiscordWebhookHandler(logging.Handler):
    def __init__(self, webhook_url: str):
        super().__init__()

        def avatar(avatar_id: int):
            return f"https://cdn.discordapp.com/embed/avatars/{avatar_id}.png"

        self.webhook = SyncWebhook.from_url(webhook_url)

        # fmt: off
        self.LOG_TYPE_USER_MAPPING = {
            logging.CRITICAL: ("CRITICAL", avatar(4)), # red
            logging.ERROR:    ("ERROR",    avatar(4)), # red
            logging.WARNING:  ("WARNING",  avatar(3)), # yellow
            logging.INFO:     ("INFO",     avatar(1)), # grey
            logging.DEBUG:    ("DEBUG",    avatar(1)), # grey
            0:                ("NOTSET",   avatar(1)), # grey
        }
        # fmt: on

    def emit(self, record: logging.LogRecord):
        message = record.getMessage()
        user = (
            self.LOG_TYPE_USER_MAPPING.get(record.levelno)
            or self.LOG_TYPE_USER_MAPPING[0]
        )

        COMMON = {
            "username": f"[{record.name.replace('discord', 'd')}] {user[0]}",
            "avatar_url": user[1],
        }

        if record.levelno < logging.ERROR and len(message) < MESSAGE_LIMIT:
            self.webhook.send(message, **COMMON)  # type: ignore
        elif len(message) - CODEBLOCK_LEN < MESSAGE_LIMIT:
            self.webhook.send(to_cb(message, lang="py"), **COMMON)  # type:ignore
        elif len(message) - CODEBLOCK_LEN < EMBED_LIMIT:
            embed = Embed(
                description=to_cb(message, lang="py"),
                timestamp=datetime.fromtimestamp(record.created),
            )

            self.webhook.send(embed=embed, **COMMON)  # type:ignore
        else:
            buffer = BytesIO()
            buffer.write(message.encode("utf-8"))
            buffer.seek(0)

            self.webhook.send(file=File(buffer, filename="log.txt"))


logger = logging.getLogger("estella")

handler = logging.StreamHandler()
handler.setFormatter(_ColourFormatter())

logger.addHandler(handler)

if LOG_FUNNEL_WEBHOOK:
    discordLogger = logging.getLogger("discord")
    discordLogger.addHandler(DiscordWebhookHandler(LOG_FUNNEL_WEBHOOK))

    logger.addHandler(DiscordWebhookHandler(LOG_FUNNEL_WEBHOOK))

logger.setLevel(logging.DEBUG)
