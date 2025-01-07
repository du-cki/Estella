from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import hashlib
import datetime

from io import BytesIO
from base64 import b64decode

from mcstatus import JavaServer
from mcstatus.status_response import JavaStatusPlayer

from utils import to_cb, motd_to_ansi, logger
from config import SERVER_IP

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from utils import Estella
    from mcstatus.status_response import JavaStatusResponse


async def _is_server_online(interaction: discord.Interaction[Estella]) -> bool:
    if SERVER_IP is None:
        raise app_commands.CheckFailure(
            "I'm not set to watch any servers at the moment."
        )

    cog: "Minecraft" = interaction.client.cogs["Minecraft"]  # type: ignore
    try:
        await cog.client.async_ping()  # type: ignore
    except Exception:
        raise app_commands.CheckFailure(
            "I can't seem to reach the server at this moment, please try again later."
        )
    else:
        return True


class Minecraft(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot

        self.HEAD_CACHE: dict[str, discord.Emoji] = {}

        # This is a bit of a hack, but it works.
        # It would lookup `None` if there is nothing but not error, since we don't want
        # the cog to be unloaded if there are no servers, we already have checks for that.
        self.client = JavaServer.lookup(str(SERVER_IP))

    def _convert_data_uri(self, data_uri: str) -> tuple[BytesIO, str]:
        header, encoded = data_uri.split(",", 1)
        data = b64decode(encoded)

        mime_type = header.split(";")[0].split(":")[1]
        ext = mime_type.split("/")[1]

        return BytesIO(data), ext

    server = app_commands.Group(
        name="server",
        description="Commands related to any minecraft server that I watch.",
    )

    async def cog_app_command_error(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        interaction: discord.Interaction[Estella],
        error: app_commands.AppCommandError,
    ):
        if isinstance(error, app_commands.CheckFailure):
            return await interaction.response.send_message(
                error.args[0],
                ephemeral=True,
            )

        raise error

    @server.command(description="Pings the server.")
    @app_commands.check(_is_server_online)
    async def ping(self, interaction: discord.Interaction[Estella]):
        latency: float = await self.client.async_ping()  # type: ignore
        await interaction.response.send_message(f"Pong! **{latency:.2f}ms**")

    @server.command(description="Views the information of the server.")
    @app_commands.check(_is_server_online)
    async def info(self, interaction: discord.Interaction[Estella]):
        status: JavaStatusResponse = await self.client.async_status()  # type: ignore

        embed = discord.Embed(
            title="Server Information",
            description=to_cb(motd_to_ansi(status.motd.parsed), lang="ansi"),
        )

        embed.add_field(
            name="Players",
            value=f"{status.players.online}/{status.players.max}",
        )

        embed.add_field(
            name="Server IP",
            value=f"`{SERVER_IP}`",
        )

        embed.add_field(
            name="Version",
            value=status.version.name,
        )

        favicon = None
        if status.favicon:
            favicon = self._convert_data_uri(status.favicon)
            embed.set_thumbnail(url=f"attachment://favicon.{favicon[1]}")

        await interaction.response.send_message(
            embed=embed,
            file=(
                discord.File(favicon[0], filename=f"favicon.{favicon[1]}")
                if favicon
                else discord.utils.MISSING
            ),
        )

    @server.command(description="List online players.")
    @app_commands.check(_is_server_online)
    async def players(self, interaction: discord.Interaction[Estella]):
        await interaction.response.defer()

        status: JavaStatusResponse = await self.client.async_status()  # type: ignore

        if not status.players.sample:
            return await interaction.response.send_message(
                "I don't see anyone online at the moment."
            )

        annons = 0
        players_list = [
            await self._format_player(player)
            for player in status.players.sample
            if player.name != "Anonymous Player"
        ]

        annons = len(status.players.sample) - len(players_list)  # rest are annons
        plularity = "players" if annons > 1 else "player"

        # when all the players are "Anonymous Player"s
        if not players_list and annons > 0:
            players = f"{annons} {plularity}"
        else:
            players = ", ".join(players_list)

            if annons > 0:
                players += f" and {annons} more {plularity}"

        result = (
            f"**{status.players.online}**/**{status.players.max}** online: {players}."
        )

        if annons > 0:
            result += "\n-# Can't see your name or others? [`Learn More`](<https://minecraft.wiki/w/Java_Edition_21w44a#General>)"

        await interaction.edit_original_response(content=result)

    async def cog_load(self):
        emojis = await self.bot.fetch_application_emojis()

        for emoji in emojis:
            if emoji.name.endswith("_head"):
                name, _ = emoji.name.rsplit("_", maxsplit=1)
                self.HEAD_CACHE[name] = emoji

        return await super().cog_load()

    async def _format_player(self, player: JavaStatusPlayer) -> str:
        name = player.name.lower()
        if name not in self.HEAD_CACHE:
            await self._create_player_head(player)

        # let it update in the background
        await self.bot.loop.create_task(
            self._validate_and_update_player_head(player),
        )

        return f"{self.HEAD_CACHE[name]} **{player.name}**"

    async def _get_player_head(
        self,
        uuid: str,
        *,
        size: int = 128,
    ) -> bytes:
        async with self.bot.session.get(
            f"https://crafthead.net/avatar/{uuid}/{size}"
        ) as req:
            return await req.read()

    async def _create_player_head(
        self,
        player: JavaStatusPlayer,
        *,
        last_updated_at: Optional[datetime.datetime] = None,
    ):
        logger.info(
            "Creating a player head emoji for: %s (%s)", player.name, player.uuid
        )

        player_head = await self._get_player_head(player.uuid)
        hash_ = hashlib.sha256(player_head).hexdigest()

        name = player.name.lower()
        emoji = await self.bot.create_application_emoji(
            name=f"{name}_head",
            image=player_head,
        )

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO minecraft_heads (uuid, emoji_hash, last_updated_at)
                    VALUES ($1, $2, $3)
                ON CONFLICT (uuid) 
                    DO UPDATE SET 
                        emoji_hash = $2,
                        last_updated_at = $3;
            """,
                player.uuid,
                hash_,
                last_updated_at or datetime.datetime.now(),
            )

        self.HEAD_CACHE[name] = emoji
        logger.info("Created the player head.")

    async def _validate_and_update_player_head(self, player: JavaStatusPlayer):
        async with self.bot.pool.acquire() as conn:
            player_data = await conn.fetchone(
                """
                SELECT *
                    FROM minecraft_heads
                WHERE
                    uuid = $1;
            """,
                player.uuid,
            )

        if not player_data:
            return

        last_updated_at = datetime.datetime.fromisoformat(
            player_data["last_updated_at"]
        )

        now = datetime.datetime.now()

        lower_limit = now - last_updated_at
        upper_limit = datetime.timedelta(minutes=10)

        if lower_limit < upper_limit:
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                """
                    UPDATE minecraft_heads
                        SET last_updated_at = $1
                        WHERE uuid = $2
                """,
                now,
                player.uuid,
            )

        player_head = await self._get_player_head(player.uuid)
        hash_ = hashlib.sha256(player_head).hexdigest()

        if player_data["emoji_hash"] == hash_:
            return

        logger.info("Updating player head for: %s (%s)", player.name, player.uuid)

        await self.HEAD_CACHE[player.uuid].delete()
        await self._create_player_head(player)


async def setup(bot: Estella):
    await bot.add_cog(Minecraft(bot))
