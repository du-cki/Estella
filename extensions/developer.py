from __future__ import annotations

import discord
from discord.ext import commands

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils import Estella


class Developer(commands.Cog):
    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context[Estella]):
        commands = await ctx.bot.tree.sync()
        await ctx.send(
            f"Synced {len(commands)} command{['s', ''][len(commands) == 1]}.",
        )

    @commands.group(aliases=["wl"], invoke_without_command=True)
    @commands.is_owner()
    async def whitelist(self, ctx: commands.Context[Estella]): ...

    @whitelist.command()
    @commands.is_owner()
    async def add(self, ctx: commands.Context[Estella], user: discord.User):
        async with ctx.bot.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO bot_whitelist
                    VALUES ($1)
                ON CONFLICT (user_id)
                    DO NOTHING
                """,
                user.id,
            )

        await ctx.send(f"Added {user.mention} to the bot whitelist.")

    @whitelist.command()
    @commands.is_owner()
    async def remove(self, ctx: commands.Context[Estella], user: discord.User):
        async with ctx.bot.pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM bot_whitelist
                WHERE user_id = $1
                """,
                user.id,
            )

        await ctx.send(f"Removed {user.mention} from the bot whitelist.")


async def setup(bot: Estella):
    await bot.add_cog(Developer(bot))
