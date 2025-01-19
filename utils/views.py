from __future__ import annotations

import traceback

import discord
from discord import ui

from .functions import to_cb
from .logging import logger

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Self
    from .subclasses import Estella

    Interaction = discord.Interaction[Estella]


class BaseView(ui.View):
    author_id: Optional[int]
    message: Optional[discord.Message]

    def __init__(
        self,
        *,
        author_id: Optional[int] = None,
        timeout: Optional[float] = 180,
    ):
        super().__init__(timeout=timeout)

        self.author_id = author_id
        self.message = None

    async def on_timeout(self) -> None:
        if self.message:
            for child in self.children:
                if isinstance(child, ui.Button | ui.Select):
                    child.disabled = True

            await self.message.edit(view=self)
        else:
            return await super().on_timeout()

    async def interaction_check(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        interaction: Interaction,
    ) -> bool:
        if self.author_id:
            pred = interaction.user.id == self.author_id
            if not pred:
                await interaction.response.send_message(
                    "This view is not for you.", ephemeral=True
                )

            return pred
        else:
            return await super().interaction_check(interaction)

    async def on_error(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        interaction: Interaction,
        error: Exception,
        item: ui.Item[Self],
    ) -> None:
        strat = (
            interaction.response.send_message
            if not interaction.response.is_done()
            else interaction.followup.send
        )

        channel = (
            f"{interaction.channel.mention} ({interaction.channel.jump_url})"
            if interaction.channel
            and not isinstance(
                interaction.channel, discord.DMChannel | discord.GroupChannel
            )
            else "<DMChannel>"
        )

        trace_back = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

        logger.error(
            "An error has occurered on view %s (item: %s) in %s for %s (%s):\n%s",
            self.__class__.__name__,
            str(item),
            channel,
            interaction.user.mention,
            interaction.user.id,
            trace_back,
        )

        is_owner = await interaction.client.is_owner(interaction.user)

        if is_owner:
            error_message = to_cb(trace_back, lang="py")
            message = f"An error has occurred!\n{error_message}"
        else:
            message = "An error has occurred, this incident has been reported."

        await strat(content=message)


class ConfirmationView(BaseView):
    def __init__(self, *, author_id: Optional[int], timeout: Optional[float] = 180):
        super().__init__(author_id=author_id, timeout=timeout)

        self.value = None

    @ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: Interaction, _: ui.Button[Self]):
        await interaction.response.defer()
        self.value = True

        self.stop()

    @ui.button(label="Abort", style=discord.ButtonStyle.danger)
    async def abort(self, interaction: Interaction, _: ui.Button[Self]):
        await interaction.response.defer()
        self.value = False

        self.stop()
