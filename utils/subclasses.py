from __future__ import annotations

import discord
from discord.ext import commands

import asqlite

from pathlib import Path
from aiohttp import ClientSession

from .logging import logger


async def whitelist_check(interaction: discord.Interaction[Estella]):
    if await interaction.client.is_owner(interaction.user):
        return True

    async with interaction.client.pool.acquire() as conn:
        whitelisted = await conn.fetchone(
            "SELECT EXISTS (SELECT 1 FROM bot_whitelist WHERE user_id = $1)",
            interaction.user.id,
        )

        whitelisted = whitelisted[0]

    if not whitelisted:
        await interaction.response.send_message(
            "You are not whitelisted. Please contact the owner to get whitelisted.",
            ephemeral=True,
        )

    return whitelisted


class Estella(commands.Bot):
    async def setup_hook(self):
        self.session = ClientSession()
        self.tree.interaction_check = whitelist_check

        logger.info("Connecting to database.")
        self.pool = await asqlite.create_pool("data.db")

        logger.info("Setting up database.")
        async with self.pool.acquire() as conn:
            with open("schema.sql") as f:
                await conn.executescript(f.read())

        await self.load_extension("jishaku")

        exts = Path("extensions").glob("*.py")
        for ext in exts:
            logger.info(f"Loading extension: {ext.name}")
            await self.load_extension(f"extensions.{ext.name[:-3]}")

        logger.info(f"Logged in as {self.user}")
