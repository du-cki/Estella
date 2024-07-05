from __future__ import annotations

import discord
from discord.ext import commands

from discord import app_commands

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Estella


class General(commands.Cog):
    @app_commands.command(description="Pings the bot.")
    async def ping(self, interaction: discord.Interaction[Estella]):
        await interaction.response.send_message("Pong!", ephemeral=True)


async def setup(bot: Estella):
    await bot.add_cog(General(bot))
