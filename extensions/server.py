from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

from io import BytesIO
from base64 import b64decode

from mcstatus import JavaServer

from utils import to_cb
from config import SERVER_IP

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Estella
    from mcstatus.status_response import JavaStatusResponse


class Server(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot
        self.client = JavaServer.lookup(SERVER_IP)

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

    @server.command(description="Pings the server.")
    async def ping(self, interaction: discord.Interaction[Estella]):
        latency: float = await self.client.async_ping()  # type: ignore

        await interaction.response.send_message(
            f"Pong! **{latency:.2f}ms**",
            # ephemeral=True,
        )

    @server.command(description="View the information of the server.")
    async def info(self, interaction: discord.Interaction[Estella]):
        status: JavaStatusResponse = await self.client.async_status()  # type: ignore

        embed = discord.Embed(
            title="Server Information",
            description=to_cb(status.motd.to_ansi(), lang="ansi"),
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
            file=discord.File(favicon[0], filename=f"favicon.{favicon[1]}")
            if favicon
            else discord.utils.MISSING,
            # ephemeral=True,
        )

    @server.command(description="List online players.")
    async def players(self, interaction: discord.Interaction[Estella]):
        status: JavaStatusResponse = await self.client.async_status()  # type: ignore

        embed = discord.Embed(
            title="Online Players",
            description="\n".join(user.name for user in status.players.sample or []),
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: Estella):
    await bot.add_cog(Server(bot))
