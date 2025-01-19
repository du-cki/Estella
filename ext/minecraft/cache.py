from __future__ import annotations

import discord

import asyncio
import datetime
import hashlib

from mcstatus import JavaServer
from mcstatus.status_response import JavaStatusResponse

from enum import IntEnum

from utils import logger, Interaction

from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from typing import Optional

    from utils import Estella

    from mcstatus.status_response import JavaStatusPlayer


class MinecraftServerType(IntEnum):
    IP = 1
    RCON = 2


class ChannelType(IntEnum):
    DMChannel = 1  # or group chat
    Guild = 2
    GuildChannel = 3
    Thread = 4


IDExtractor = Callable[[Interaction], Optional[tuple[int, Optional[int]]]]

HIERARCHY: list[tuple[ChannelType, IDExtractor]] = [
    (
        ChannelType.DMChannel,
        lambda i: (
            (i.channel.id, None)
            if isinstance(i.channel, discord.abc.PrivateChannel)
            else None
        ),
    ),
    (
        ChannelType.Thread,
        lambda i: (
            (i.channel.id, i.channel.parent_id)
            if isinstance(i.channel, discord.Thread)
            else None
        ),
    ),
    (
        ChannelType.GuildChannel,
        lambda i: (
            (i.channel.id, None)
            if isinstance(i.channel, discord.abc.GuildChannel | discord.Thread)
            else None
        ),
    ),
    (
        ChannelType.Guild,
        lambda i: ((i.guild.id, None) if i.guild is not None else None),
    ),
]


class MinecraftServer:
    def __init__(self, ip: str):
        self.ip = ip
        self.__server = JavaServer.lookup(ip)

    async def ping(self) -> float:
        return (
            await self.__server.async_ping()  # pyright: ignore[reportUnknownMemberType]
        )

    async def status(self) -> JavaStatusResponse:
        return (
            await self.__server.async_status()  # pyright: ignore[reportUnknownMemberType]
        )


class MinecraftServerCache:
    def __init__(self, bot: Estella):
        self.bot = bot

    async def is_any_server_assigned(
        self,
        channel_id: int,
        channel_type: ChannelType,
        *,
        parent_channel_id: Optional[int] = None,
    ) -> bool:
        async with self.bot.pool.acquire() as conn:
            assigned = await conn.fetchone(
                """
                SELECT EXISTS(
                    SELECT 1 FROM minecraft_servers 
                        WHERE assigned_to = $1
                        AND   channel_type = $2
                        AND   parent_id IS $3
                )
            """,
                channel_id,
                channel_type.value,
                parent_channel_id,
            )

        return bool(assigned[0])

    async def assign_or_update(
        self,
        server_ip: str,
        *,
        channel_id: int,
        channel_type: ChannelType,
        assigned_by: int,
        parent_id: Optional[int] = None,
        minecraft_server_type: MinecraftServerType = MinecraftServerType.IP,
    ):
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO minecraft_servers (
                    assigned_to, parent_id, assigned_by, 
                    channel_type, minecraft_server_type, ip
                )
                    VALUES (
                        $1, $2, $3, 
                        $4, $5, $6
                    )
                ON CONFLICT (assigned_to) 
                    DO UPDATE SET
                        parent_id = $2, 
                        assigned_by = $3,
                        channel_type = $4,
                        minecraft_server_type = $5, 
                        ip = $6;
            """,
                channel_id,
                parent_id,
                assigned_by,
                channel_type.value,
                minecraft_server_type.value,
                server_ip,
            )

    async def get(
        self,
        interaction: Interaction,
    ) -> Optional[MinecraftServer]:
        applicable_hierarchy = [
            (channel_type, extracted_ids)
            for channel_type, id_extractor in HIERARCHY
            if (extracted_ids := id_extractor(interaction)) is not None
        ]

        async with self.bot.pool.acquire() as conn:
            for channel_type, (channel_id, parent_channel_id) in applicable_hierarchy:
                server_ip = await conn.fetchone(
                    """
                    SELECT ip
                        FROM minecraft_servers
                    WHERE 
                        assigned_to = $1
                    AND channel_type = $2
                    AND parent_id IS $3;
                """,
                    channel_id,
                    channel_type.value,
                    parent_channel_id,
                )

                if server_ip:
                    return MinecraftServer(server_ip[0])

        return None

    async def fetch(
        self,
        interaction: Interaction,
    ) -> MinecraftServer:
        server = await self.get(interaction)
        if not server:
            raise ValueError

        return server


class MinecraftHeadCache:
    def __init__(self, bot: Estella):
        self.bot = bot
        self._cache: dict[str, discord.Emoji] = {}
        self._lock = asyncio.Lock()

    async def get(
        self,
        player: JavaStatusPlayer,
        *,
        update: Optional[bool] = False,
        create: Optional[bool] = False,
    ) -> discord.Emoji:
        name = player.name.lower()

        emoji = self._cache.get(name)
        if emoji:
            if update:
                await self.bot.loop.create_task(
                    self._validate_and_update(player)
                )  # update in the background

            return emoji

        if not create:
            raise ValueError(f"{name}'s player head not found.")

        await self.create(player)

        return await self.get(player)

    async def populate(self):
        emojis = await self.bot.fetch_application_emojis()

        for emoji in emojis:
            if emoji.name.endswith("_head"):
                name, _ = emoji.name.rsplit("_", maxsplit=1)

                self._cache[name] = emoji

    async def fetch(
        self,
        uuid: str,
        *,
        size: int = 128,
    ) -> bytes:
        async with self.bot.session.get(
            f"https://crafthead.net/avatar/{uuid}/{size}"
        ) as req:
            return await req.read()

    async def create(
        self,
        player: JavaStatusPlayer,
        *,
        last_updated_at: Optional[datetime.datetime] = None,
    ):
        async with self._lock:
            name = player.name.lower()
            if name in self._cache:
                return

            logger.debug("Creating a player head emoji for: %s (%s)", name, player.uuid)

            player_head = await self.fetch(player.uuid)
            hash_ = hashlib.sha256(player_head).hexdigest()

            emoji = await self.bot.create_application_emoji(
                name=f"{name}_head",
                image=player_head,
            )

            async with self.bot.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO minecraft_heads (uuid, emoji_hash, last_updated_at)
                        VALUES ($1, $2, $3)
                    ON CONFLICT (uuid) 
                        DO UPDATE SET 
                            emoji_hash = $2,
                            last_updated_at = $3;
                """,
                    player.uuid,
                    hash_,
                    last_updated_at or datetime.datetime.now(),
                )

            self._cache[name] = emoji
            logger.debug("Created the player head.")

    async def delete(self, name: str):
        emoji = self._cache.pop(name)
        await emoji.delete()

    async def _validate_and_update(
        self,
        player: JavaStatusPlayer,
    ):
        async with self.bot.pool.acquire() as conn:
            player_data = await conn.fetchone(
                """
                SELECT *
                    FROM minecraft_heads
                WHERE
                    uuid = $1;
            """,
                player.uuid,
            )

        if not player_data:
            return

        last_updated_at = datetime.datetime.fromisoformat(
            player_data["last_updated_at"]
        )

        now = datetime.datetime.now()

        lower_limit = now - last_updated_at
        upper_limit = datetime.timedelta(minutes=10)

        if lower_limit < upper_limit:
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                """
                    UPDATE
                        minecraft_heads
                    SET
                        last_updated_at = $1
                    WHERE
                        uuid = $2
                """,
                now,
                player.uuid,
            )

        player_head = await self.fetch(player.uuid)
        hash_ = hashlib.sha256(player_head).hexdigest()

        if player_data["emoji_hash"] == hash_:
            return

        logger.debug("Updating player head for: %s (%s)", player.name, player.uuid)

        await self.delete(player.name.lower())
        await self.create(player)
