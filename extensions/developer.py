from __future__ import annotations

from discord.ext import commands

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Estella


class Developer(commands.Cog):
    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context[Estella]):
        commands = await ctx.bot.tree.sync()
        await ctx.send(
            f"Synced {len(commands)} command{['s', ''][len(commands) == 1]}.",
        )


async def setup(bot: Estella):
    await bot.add_cog(Developer(bot))
