from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Estella



class Time(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot

    time = app_commands.Group(
        name="time",
        description="Commands related to time.",
    )

    @time.command(name="set")
    async def _set(self, interaction: discord.Interaction[Estella]):
        ...

    @time.command(name="get")
    async def _get(self, interaction: discord.Interaction[Estella]):
        ...


async def setup(bot: Estella):
    await bot.add_cog(Time(bot))
