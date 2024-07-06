from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import zoneinfo
import itertools

from fuzzywuzzy import process  # pyright: ignore[reportMissingTypeStubs]
from pytz import timezone as tz

from typing import TYPE_CHECKING, Optional

from utils import ordinal

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

    return [
        app_commands.Choice(name=timezone, value=timezone)  # pyright: ignore[reportUnknownArgumentType]
        for timezone, _ in process.extract(current, TIMEZONES, limit=25)  # pyright: ignore[reportUnknownMemberType, reportAssignmentType, reportUnknownVariableType]
    ]


@app_commands.context_menu(name="Get Time")
async def get_time(interaction: discord.Interaction[Estella], user: discord.Member):
    cog: "Time" = interaction.client.cogs["Time"]  # pyright: ignore[reportAssignmentType]
    time = await cog.get_time_formatted(user)

    await interaction.response.send_message(
        f"{user.display_name}'s current time is {time}"
    )


class Time(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot
        self.bot.tree.add_command(get_time)

    async def get_time_formatted(
        self,
        user: discord.User | discord.Member,
    ) -> Optional[str]:
        async with self.bot.pool.acquire() as conn:
            timezone = await conn.fetchone(
                """
                SELECT timezone
                    FROM user_timezones
                WHERE user_id = $1
                """,
                user.id,
            )

        if not timezone:
            return None

        time = discord.utils.utcnow().astimezone(tz(timezone[0]))
        return time.strftime(f"**%I:%M %p** (%B {ordinal(time.day)})")

    time = app_commands.Group(
        name="time",
        description="Commands related to time.",
    )

    @time.command(name="set", description="Set your timezone.")
    @app_commands.describe(timezone="The timezone to set.")
    @app_commands.autocomplete(timezone=timezone_auto_complete)
    async def _set(
        self,
        interaction: discord.Interaction[Estella],
        timezone: str,
    ):
        if timezone not in TIMEZONES:
            return await interaction.response.send_message(
                f"`{timezone}` is not a valid timezone.",
                ephemeral=True,
            )

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_timezones
                    VALUES ($1, $2)
                ON CONFLICT (user_id)
                    DO UPDATE SET timezone = $2
                """,
                interaction.user.id,
                timezone,
            )

        await interaction.response.send_message(
            f"Done! I've set your timezone as `{timezone}`",
            ephemeral=True,
        )

    @time.command(name="info", description="Get the time of a specific timezone.")
    @app_commands.describe(timezone="The timezone to get the time of.")
    @app_commands.autocomplete(timezone=timezone_auto_complete)
    async def _info(
        self,
        interaction: discord.Interaction[Estella],
        timezone: str,
        hidden: bool = False,
    ):
        if timezone not in TIMEZONES:
            return await interaction.response.send_message(
                f"`{timezone}` is not a valid timezone.",
                ephemeral=False,
            )

        time = discord.utils.utcnow().astimezone(tz(timezone))
        formatted = time.strftime(f"**%I:%M %p** (%B {ordinal(time.day)})")

        await interaction.response.send_message(
            f"The time in `{timezone}` is {formatted}",
            ephemeral=hidden,
        )

    @time.command(name="get", description="Get a user's set timezone.")
    @app_commands.describe(
        user="The user to get the timezone of, or leave it blank for yourself.",
        hidden="Whether or not to hide the response.",
    )
    async def _get(
        self,
        interaction: discord.Interaction[Estella],
        user: Optional[discord.User] = None,
        hidden: bool = False,
    ):
        target = user or interaction.user
        time = await self.get_time_formatted(target)

        await interaction.response.send_message(
            f"{target.display_name}'s current time is {time}",
            ephemeral=hidden,
        )


async def setup(bot: Estella):
    await bot.add_cog(Time(bot))
