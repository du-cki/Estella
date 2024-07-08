import discord
from discord import app_commands

from discord.ext import commands

from utils import Estella
from config import TOKEN


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
