from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

from io import BytesIO
from base64 import b64decode

from mcstatus import JavaServer

from utils import to_cb, motd_to_ansi
from config import SERVER_IP

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils import Estella
    from mcstatus.status_response import JavaStatusResponse


async def _is_server_online(interaction: discord.Interaction[Estella]) -> bool:
    if SERVER_IP is None:
        raise app_commands.CheckFailure(
            "I'm not set to watch any servers at the moment."
        )

    cog: "Server" = interaction.client.cogs["Server"]  # type: ignore
    try:
        await cog.client.async_ping()  # type: ignore
    except Exception:
        raise app_commands.CheckFailure(
            "I can't seem to reach the server at this moment, please try again later."
        )
    else:
        return True


class Server(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot

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
        description="Commands related to the server.",
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

    @server.command(description="View the information of the server.")
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
        status: JavaStatusResponse = await self.client.async_status()  # type: ignore

        if not status.players.sample:
            return await interaction.response.send_message(
                "I don't see anyone online at the moment."
            )

        embed = discord.Embed(
            title="Online Players",
            description="\n".join(user.name for user in status.players.sample),
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: Estella):
    await bot.add_cog(Server(bot))
