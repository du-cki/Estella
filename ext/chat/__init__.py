from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from .ddg import DDG

if TYPE_CHECKING:
    from utils import Estella


class Chat(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot
        self.DDG = DDG(self.bot.session)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        user = self.bot.user
        ctx = await self.bot.get_context(message)

        if ctx.valid or not user:
            return

        name = user.name.lower()

        cnt = message.content
        if not cnt.lower().startswith(name):
            return

        query = cnt[len(name) :].strip()
        if not query:
            return

        blacklisted = await self.bot.is_user_blacklisted(message.author.id)
        if blacklisted:
            return

        async with ctx.typing():
            if answer := await self.DDG.query(query):
                return await message.channel.send(answer)

            await message.channel.send("idk")


async def setup(bot: Estella):
    await bot.add_cog(Chat(bot))
