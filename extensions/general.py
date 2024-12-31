from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils import Estella


class General(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot

    @app_commands.command(description="Pings the bot.")
    async def ping(self, interaction: discord.Interaction[Estella]):
        await interaction.response.send_message(
            f"Pong! **{interaction.client.latency * 1000:.2f}ms**",
            ephemeral=True,
        )


async def setup(bot: Estella):
    await bot.add_cog(General(bot))
