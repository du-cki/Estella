from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import zoneinfo
import itertools

from fuzzywuzzy import process  # pyright: ignore[reportMissingTypeStubs]
from pytz import timezone as tz, BaseTzInfo

from datetime import datetime

from typing import TYPE_CHECKING, Optional

from utils import ordinal

if TYPE_CHECKING:
    from utils import Estella

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

    try:
        time = await cog.get_user_time(user)
    except app_commands.CheckFailure as err:
        await interaction.response.send_message(err.args[0], ephemeral=True)
    else:
        await interaction.response.send_message(
            f"{user.display_name}'s current time is {time}"
        )


class Time(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot
        self.bot.tree.add_command(get_time)

    async def get_user_time(
        self,
        user: discord.User | discord.Member,
        *,
        formatted: bool = True,
    ) -> str | BaseTzInfo:
        if user.bot:
            raise app_commands.CheckFailure("Bots dont have timezones, dummy!")

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
            raise app_commands.CheckFailure("This user has no timezone set.")

        timezone = tz(timezone[0])

        return self.format_timezone(timezone) if formatted else timezone

    def format_timezone(self, timezone: BaseTzInfo) -> str:
        time = discord.utils.utcnow().astimezone(timezone)
        return time.strftime(f"**%I:%M %p** (%B {ordinal(time.day)})")

    timezone = app_commands.Group(
        name="timezone",
        description="Commands related to time.",
    )

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction[discord.Client],
        error: app_commands.AppCommandError,
    ) -> None:
        if isinstance(error, app_commands.CheckFailure):
            return await interaction.response.send_message(
                error.args[0],
                ephemeral=True,
            )

        raise error

    @timezone.command(name="set", description="Set your timezone.")
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

    @timezone.command(name="info", description="Get the time of a specific timezone.")
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

        formatted = self.format_timezone(tz(timezone))
        await interaction.response.send_message(
            f"The time in `{timezone}` is {formatted}",
            ephemeral=hidden,
        )

    @timezone.command(name="get", description="Get a user's set timezone.")
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

        time = await self.get_user_time(target)
        await interaction.response.send_message(
            f"{target.display_name}'s current time is {time}",
            ephemeral=hidden,
        )

    @timezone.command(
        name="compare", description="Compare your timezone against someone."
    )
    @app_commands.describe(user="The user to compare against.")
    async def _compare(
        self,
        interaction: discord.Interaction[Estella],
        user: discord.User,
        hidden: bool = False,
    ):
        author_timezone = await self.get_user_time(interaction.user, formatted=False)
        target_timezone = await self.get_user_time(user, formatted=False)

        assert isinstance(author_timezone, BaseTzInfo) and isinstance(
            target_timezone, BaseTzInfo
        )

        now = datetime.now()

        author_tz_offset, target_tz_offset = (
            now.astimezone(author_timezone).utcoffset(),
            now.astimezone(target_timezone).utcoffset(),
        )

        if not author_tz_offset or not target_tz_offset:  # type check
            raise app_commands.CheckFailure(
                "I can't compare timezones that don't exist."
            )

        delta = (target_tz_offset - author_tz_offset).total_seconds() / 3600

        message = None
        if delta == 0:
            message = "the same as yours."
        elif delta > 0:
            message = f"{abs(delta)} hours ahead of you."
        else:
            message = f"{abs(delta)} hours behind you."

        await interaction.response.send_message(
            f"{user.display_name}'s time is {message}",
            ephemeral=hidden,
        )


async def setup(bot: Estella):
    await bot.add_cog(Time(bot))
