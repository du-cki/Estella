from __future__ import annotations

import discord
from discord import ui

from .cache import ChannelType, MinecraftServerType
from utils.views import BaseView

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from typing import Any

    from . import Minecraft
    from utils import Interaction


channel_phrasing: dict[ChannelType, str] = {
    ChannelType.DMChannel: "This Channel",
    ChannelType.Guild: "This Server",
    ChannelType.GuildChannel: "This Channel",
    ChannelType.Thread: "This Thread",
}


class ChannelSource(ui.Select["AssignSourceView"]):
    def __init__(
        self,
        server_ip: str,
        channel_options: dict[str, ChannelType],
        *args: Any,
        **kwargs: Any,
    ):
        options = [
            discord.SelectOption(label=label, value=str(value.value))
            for (label, value) in channel_options.items()
        ]

        self.server_ip = server_ip

        super().__init__(
            options=options,
            *args,
            **kwargs,
        )

    async def callback(self, interaction: Interaction):
        channel_type = ChannelType(int(self.values[0]))
        cog = cast("Minecraft", interaction.client.cogs["Minecraft"])

        parent_id = None
        if channel_type == ChannelType.Thread and isinstance(
            interaction.channel, discord.Thread
        ):
            id_ = interaction.channel.id
            parent_id = interaction.channel.parent_id
        elif channel_type == ChannelType.GuildChannel and interaction.channel:
            id_ = interaction.channel.id
        elif channel_type == ChannelType.Guild and interaction.guild:
            id_ = interaction.guild.id
        else:
            raise ValueError

        is_assigned_elsewhere = await cog.minecraft_server_cache.is_any_server_assigned(
            id_, channel_type, parent_channel_id=parent_id
        )

        data: dict[str, Any] = {
            "server_ip": self.server_ip,
            "channel_id": id_,
            "channel_type": channel_type,
            "parent_id": parent_id,
            "minecraft_server_type": MinecraftServerType.IP,
        }

        if is_assigned_elsewhere:
            if self.view:
                self.view.stop()

            return await cog.ask_for_reassignment_confirmation(interaction, **data)

        await cog.minecraft_server_cache.assign_or_update(self.server_ip, **data)

        await interaction.response.edit_message(
            content=f"Assigned **`{self.server_ip}`** to {channel_phrasing[channel_type].lower()}.",
            view=None,
        )

        if self.view:
            self.view.stop()


class AssignSourceView(BaseView):
    def __init__(
        self,
        server_ip: str,
        channel: discord.abc.GuildChannel | discord.Thread,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        self.server_ip = server_ip
        self.guild = channel.guild
        self.channel = channel

        options: dict[str, ChannelType] = {
            "This Server": ChannelType.Guild,
            "This Channel": ChannelType.GuildChannel,
        }

        if isinstance(channel, discord.Thread):
            options["This Thread"] = ChannelType.Thread

        self.add_item(
            ChannelSource(
                self.server_ip,
                options,
                placeholder="Context",
                min_values=1,
                max_values=1,
            )
        )
