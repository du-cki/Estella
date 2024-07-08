import discord
from discord import app_commands

from discord.ext import commands

import asqlite

from pathlib import Path
from aiohttp import ClientSession

from utils import logger
from config import TOKEN


class Estella(commands.Bot):
    async def setup_hook(self):
        self.session = ClientSession()

        logger.info("Connecting to database.")
        self.pool = await asqlite.create_pool("data.db")

        logger.info("Setting up database.")
        async with self.pool.acquire() as conn:
            with open("schema.sql") as f:
                await conn.executescript(f.read())

        await self.load_extension("jishaku")

        exts = Path("extensions").glob("*.py")
        for ext in exts:
            logger.info(f"Loading extension: {ext.name}")
            await self.load_extension(f"extensions.{ext.name[:-3]}")

        logger.info(f"Logged in as {self.user}")


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
