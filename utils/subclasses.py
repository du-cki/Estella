from __future__ import annotations

import discord
from discord.ext import commands

from discord.http import handle_message_parameters
from discord.flags import MessageFlags

import glob
import json
import asqlite

from aiohttp import ClientSession

from .logging import logger

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


async def blacklist_check(interaction: discord.Interaction[Estella]):
    # if await interaction.client.is_owner(interaction.user):
    #     return True

    async with interaction.client.pool.acquire() as conn:
        blacklisted = await conn.fetchone(
            "SELECT EXISTS (SELECT 1 FROM bot_blacklist WHERE user_id = $1)",
            interaction.user.id,
        )

        blacklisted = blacklisted[0]

    if blacklisted:
        await interaction.response.send_message(
            "You are blacklisted. Please contact the owner to get whitelisted again.",
            ephemeral=True,
        )

        return False

    return True


class Estella(commands.Bot):
    async def setup_hook(self):
        self.session = ClientSession()
        self.tree.interaction_check = blacklist_check

        logger.info("Connecting to database.")
        self.pool = await asqlite.create_pool("db/data.db")

        logger.info("Setting up database.")
        async with self.pool.acquire() as conn:
            with open("schema.sql") as f:
                await conn.executescript(f.read())

        await self.load_extension("jishaku")

        exts = glob.glob("ext/[!_]*")
        for ext in exts:
            ext = ext.replace("\\", ".").replace("/", ".").removesuffix(".py")

            logger.info(f"Loading extension: {ext}")
            await self.load_extension(ext)

        logger.info(f"Logged in as {self.user}")

    async def send_voice_message(
        self,
        channel_id: int,
        file: discord.File,
        *,
        waveform: str,
        duration_secs: float,
        reference: Optional[discord.Message] = None,
    ):
        flags = MessageFlags._from_value(  # pyright: ignore[reportUnknownMemberType,reportPrivateUsage]
            8192
        )

        with handle_message_parameters(
            flags=flags,
            file=file,
            message_reference=(
                reference.to_message_reference_dict() if reference else None
            ),
        ) as params:
            assert params.multipart

            data = json.loads(params.multipart[0]["value"])

            data["attachments"][0]["waveform"] = waveform
            data["attachments"][0]["duration_secs"] = duration_secs

            params.multipart[1]["content_type"] = "audio/ogg"
            params.multipart[0]["value"] = json.dumps(data)

            await self.http.send_message(channel_id, params=params)

    async def close(self):
        logger.info("Cleaning up...")

        await super().close()
        await self.session.close()
        await self.pool.close()

        logger.info("Exiting.")
