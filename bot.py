import discord
from discord import app_commands

from discord.ext import commands

import aiohttp
import logging
import pathlib

from config import TOKEN

logger = logging.getLogger("discord")


class Estella(commands.Bot):
    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        await self.load_extension("jishaku")

        exts = pathlib.Path("extensions").glob("*.py")
        for ext in exts:
            logger.info(f"Loading extension: {ext.name}")
            await self.load_extension(f"extensions.{ext.name[:-3]}")

        logger.info(f"Logging in as {self.user}...")


bot = Estella(
    command_prefix=commands.when_mentioned,
    intents=discord.Intents.default(),
    allowed_contexts=app_commands.AppCommandContext(
        dm_channel=True,
        private_channel=True,
    ),
    allowed_installs=app_commands.AppInstallationType(user=True),
)


bot.run(TOKEN)
