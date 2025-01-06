from __future__ import annotations

import discord
from discord.ext import commands

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from utils import Estella


class Developer(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx: commands.Context[Estella]):
        commands = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(commands)} command{['s', ''][len(commands) == 1]}.",
        )

    @commands.group(aliases=["bl"], invoke_without_command=True, hidden=True)
    @commands.is_owner()
    async def blacklist(self, ctx: commands.Context[Estella]):
        await ctx.send_help(self.blacklist)

    @blacklist.command()
    @commands.is_owner()
    async def add(
        self,
        ctx: commands.Context[Estella],
        user: discord.User,
        *,
        reason: Optional[str],
    ):
        async with ctx.bot.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO bot_blacklist
                    VALUES ($1, $2)
                ON CONFLICT (user_id)
                    DO NOTHING
                """,
                user.id,
                reason,
            )

        await ctx.send(f"Added {user.mention} to the bot blacklist.")

    @blacklist.command()
    @commands.is_owner()
    async def remove(self, ctx: commands.Context[Estella], user: discord.User):
        async with ctx.bot.pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM bot_blacklist
                WHERE user_id = $1
                """,
                user.id,
            )

        await ctx.send(f"Removed {user.mention} from the bot blacklist.")

    async def is_owner(self, user_id: int) -> bool:
        if self.bot.owner_id:
            return user_id == self.bot.owner_id

        if self.bot.owner_ids:
            return user_id in self.bot.owner_ids

        # this would only be called once and would be a cached call later.
        user = await self.bot.fetch_user(user_id)
        return await self.bot.is_owner(user)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # 🗑️
        if (
            self.bot.user
            and payload.emoji.name[:-1] == "\U0001f5d1"
            and await self.is_owner(payload.user_id)
            and payload.message_author_id == self.bot.user.id
        ):
            await self.bot.http.delete_message(payload.channel_id, payload.message_id)


async def setup(bot: Estella):
    await bot.add_cog(Developer(bot))
