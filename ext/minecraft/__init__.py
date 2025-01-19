from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands
from mcstatus.status_response import JavaStatusPlayer

from utils import to_cb, motd_to_ansi, convert_data_uri
from utils.views import ConfirmationView

from .views import (
    channel_phrasing,
    AssignSourceView,
    ChannelType,
    MinecraftServerType,
)

from .cache import (
    MinecraftHeadCache,
    MinecraftServer,
    MinecraftServerCache,
)

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from utils import Estella, Interaction


async def _is_server_online(interaction: Interaction) -> bool:
    assert interaction.channel

    cog: "Minecraft" = interaction.client.cogs[
        "Minecraft"
    ]  # pyright: ignore[reportAssignmentType]

    server = await cog.minecraft_server_cache.get(interaction)
    if not server:
        raise app_commands.CheckFailure("I'm not set to watch any contexts here.")

    try:
        await server.ping()
    except Exception:
        raise app_commands.CheckFailure(
            "I can't seem to reach the server at this moment, please try again later."
        )
    else:
        return True


class Minecraft(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot
        self.minecraft_server_cache = MinecraftServerCache(bot)
        self.minecraft_head_cache = MinecraftHeadCache(bot)

    async def cog_load(self):
        await self.minecraft_head_cache.populate()

        return await super().cog_load()

    async def cog_app_command_error(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        interaction: Interaction,
        error: app_commands.AppCommandError,
    ):
        strat = (
            interaction.response.send_message
            if not interaction.response.is_done()
            else interaction.followup.send
        )

        if isinstance(error, app_commands.CheckFailure):
            return await strat(
                content=error.args[0],
                ephemeral=True,
            )

        raise error

    server = app_commands.Group(
        name="server",
        description="Commands related to any minecraft server that I watch.",
    )

    async def ask_for_reassignment_confirmation(
        self,
        interaction: Interaction,
        *,
        server_ip: str,
        channel_id: int,
        channel_type: ChannelType,
        parent_id: Optional[int] = None,
        minecraft_server_type: MinecraftServerType = MinecraftServerType.IP,
    ):
        strat = (
            interaction.response.edit_message
            if not interaction.response.is_done()
            else interaction.edit_original_response
        )

        view = ConfirmationView(author_id=interaction.user.id)
        view.message = await strat(
            content=f"There seems to be a server assigned to {channel_phrasing[channel_type].lower()} already, do you want to overwrite it?",
            view=view,
        )

        await view.wait()

        if view.value is True:
            await self.minecraft_server_cache.assign_or_update(
                server_ip,
                channel_id=channel_id,
                channel_type=channel_type,
                parent_id=parent_id,
                minecraft_server_type=minecraft_server_type,
                assigned_by=interaction.user.id,
            )

            await interaction.edit_original_response(
                content=f"I've updated the assigned server in {channel_phrasing[channel_type].lower()} to **`{server_ip}`**.",
                view=None,
            )
        else:
            await interaction.edit_original_response(
                content="Aborted.",
                view=None,
            )

    @server.command(description="Assign a Minecraft Server to a channnel.")
    @app_commands.describe(minecraft_server_ip="The Minecraft Server IP.")
    async def assign(
        self,
        interaction: Interaction,
        minecraft_server_ip: str,
    ):
        assert interaction.channel

        owner = await interaction.client.is_owner(interaction.user)

        if isinstance(interaction.channel, discord.GroupChannel):
            if not (interaction.user == interaction.channel.owner or owner):
                raise app_commands.CheckFailure(
                    "This is command is restricted to the group leader, or an authorized personel."
                )

        if isinstance(
            interaction.channel, (discord.abc.GuildChannel, discord.Thread)
        ) and isinstance(interaction.user, discord.Member):
            permissions = interaction.channel.permissions_for(interaction.user)

            if not (
                permissions.manage_channels
                or owner
                or (
                    isinstance(interaction.channel, discord.Thread)
                    and interaction.channel.owner
                )
            ):
                error_message = (
                    "This command is restricted to members with **Manage Channels** permissions, "
                    "the thread owner (if applicable), or authorized personnel."
                )

                raise app_commands.CheckFailure(error_message)

        await interaction.response.defer()

        try:
            server = MinecraftServer(minecraft_server_ip)

            await server.ping()
        except Exception:
            return await interaction.edit_original_response(
                content=f"I can't seem to reach **`{minecraft_server_ip}`**."
            )

        # dm or group chat
        if isinstance(interaction.channel, discord.abc.PrivateChannel):
            channel_type = ChannelType.DMChannel

            any_server_assigned = (
                await self.minecraft_server_cache.is_any_server_assigned(
                    interaction.channel.id,
                    channel_type,
                )
            )

            if any_server_assigned:
                await self.ask_for_reassignment_confirmation(
                    interaction,
                    server_ip=minecraft_server_ip,
                    channel_id=interaction.channel.id,
                    channel_type=channel_type,
                    parent_id=None,
                    minecraft_server_type=MinecraftServerType.IP,
                )
            else:
                await self.minecraft_server_cache.assign_or_update(
                    server_ip=minecraft_server_ip,
                    channel_id=interaction.channel.id,
                    channel_type=channel_type,
                    parent_id=None,
                    minecraft_server_type=MinecraftServerType.IP,
                    assigned_by=interaction.user.id,
                )

                await interaction.edit_original_response(
                    content=f"Assigned **`{minecraft_server_ip}`** to this channel."
                )
        else:
            assert isinstance(interaction.user, discord.Member)

            view = AssignSourceView(
                minecraft_server_ip,
                interaction.channel,
                author_id=interaction.user.id,
            )

            view.message = await interaction.edit_original_response(
                content="Where should I assign this server to?",
                view=view,
            )

    @server.command(description="Pings the server.")
    @app_commands.check(_is_server_online)
    async def ping(self, interaction: Interaction):
        server = await self.minecraft_server_cache.fetch(interaction)
        latency = await server.ping()

        await interaction.response.send_message(f"Pong! **{latency:.2f}ms**")

    @server.command(description="Views the information of the server.")
    @app_commands.check(_is_server_online)
    async def info(self, interaction: Interaction):
        server = await self.minecraft_server_cache.fetch(interaction)
        status = await server.status()

        embed = (
            discord.Embed(
                title="Server Information",
                description=to_cb(motd_to_ansi(status.motd.parsed), lang="ansi"),
            )
            .add_field(
                name="Players",
                value=f"{status.players.online}/{status.players.max}",
            )
            .add_field(
                name="Server IP",
                value=f"**`{server.ip}`**",
            )
            .add_field(
                name="Version",
                value=status.version.name,
            )
            .set_image(url="https://i.imgur.com/IfBmnOp.png")
        )

        favicon = None
        if status.favicon:
            favicon = convert_data_uri(status.favicon)
            embed.set_thumbnail(url=f"attachment://favicon.{favicon[1]}")

        await interaction.response.send_message(
            embed=embed,
            file=(
                discord.File(favicon[0], filename=f"favicon.{favicon[1]}")
                if favicon
                else discord.utils.MISSING
            ),
        )

    async def _format_player(self, player: JavaStatusPlayer) -> str:
        head = await self.minecraft_head_cache.get(player)
        return f"{head} **{player.name}**"

    @server.command(description="List online players.")
    @app_commands.check(_is_server_online)
    async def players(self, interaction: Interaction):
        await interaction.response.defer()

        server = await self.minecraft_server_cache.fetch(interaction)
        status = await server.status()

        if not status.players.sample:
            await interaction.edit_original_response(
                content="I don't see anyone online at the moment."
            )

            return

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


async def setup(bot: Estella):
    await bot.add_cog(Minecraft(bot))
