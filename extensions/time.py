from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import zoneinfo
import itertools

from fuzzywuzzy import process  # pyright: ignore[reportMissingTypeStubs]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Estella

TIMEZONES = zoneinfo.available_timezones()


async def timezone_auto_complete(
    _interaction: discord.Interaction[Estella],
    current: str,
) -> list[app_commands.Choice[str]]:
    if not current:
        return [
            app_commands.Choice(name=timezone, value=timezone)
            for timezone in itertools.islice(TIMEZONES, 25)
        ]

    if current not in TIMEZONES:
        return []

    return [
        app_commands.Choice(name=timezone, value=timezone)
        for (i, timezone) in process.extract(current, TIMEZONES, limit=25)  # type: ignore
    ]


class Time(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot

    time = app_commands.Group(
        name="time",
        description="Commands related to time.",
    )

    @time.command(name="set")
    @app_commands.autocomplete(timezone=timezone_auto_complete)
    async def _set(self, interaction: discord.Interaction[Estella], timezone: str):
        if timezone not in TIMEZONES:
            return await interaction.response.send_message(
                f"`{timezone}` is not a valid timezone.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            f"You selected `{timezone}`!",
            ephemeral=True,
        )

    @time.command(name="get")
    async def _get(self, interaction: discord.Interaction[Estella]): ...


async def setup(bot: Estella):
    await bot.add_cog(Time(bot))
