import jishaku

import discord
from discord import app_commands

from discord.ext import commands

from utils import Estella, variants
from config import TOKEN, DEFAULT_PREFIX

jishaku.Flags.NO_UNDERSCORE = True
jishaku.Flags.HIDE = True
jishaku.Flags.NO_DM_TRACEBACK = True

intents = discord.Intents.all()


bot = Estella(
    command_prefix=commands.when_mentioned_or(*variants(DEFAULT_PREFIX)),
    strip_after_prefix=True,
    case_insensitive=True,
    intents=intents,
    allowed_contexts=app_commands.AppCommandContext(
        dm_channel=True,
        private_channel=True,
        guild=True,
    ),
    allowed_installs=app_commands.AppInstallationType(
        user=True,
        guild=True,
    ),
)


bot.run(TOKEN)
