from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import re
import io
import csv

from utils import Timer

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils import Estella


HINT_RE = re.compile("The pokémon is (?P<hint>.*).")


@app_commands.context_menu(name="Guess Pokemon")
async def guess_pokemon(
    interaction: discord.Interaction[Estella], message: discord.Message
):
    cog: "Hint" = interaction.client.cogs["Hint"]  # pyright: ignore[reportAssignmentType]

    try:
        guesses = cog.guess_message(message)

        if len(guesses) > 1:
            await interaction.response.send_message(
                f"I've narrowed it down to these `{len(guesses)}` guesses:\n"
                + ", ".join(f"\U0001f1ec\U0001f1e7 **{guess}**" for guess in guesses),
                ephemeral=True,
            )
        else:
            formatted: dict[str, str] = {
                cog.flags[k]: v for k, v in cog.pokemon_table[guesses[0]].items()
            }

            await interaction.response.send_message(
                f"\U0001f1ec\U0001f1e7 **{guesses[0]}**, "
                + ", ".join(  # so the english name is always first.
                    f"{k} **{v}**" for k, v in formatted.items() if v
                ),
                ephemeral=True,
            )
    except Exception as err:
        await interaction.response.send_message(err.args[0], ephemeral=True)


class Hint(commands.Cog):
    def __init__(self, bot: Estella) -> None:
        super().__init__()
        self.bot = bot

        self.bot.tree.add_command(guess_pokemon)

        self.pokemon_table: dict[str, dict[str, str]] = {}
        self.flags = {
            # "en": "\U0001f1ec\U0001f1e7",
            "ja": "\U0001f1ef\U0001f1f5",
            "ja_r": "\U0001f1ef\U0001f1f5",
            "ja_t": "\U0001f1ef\U0001f1f5",
            "de": "\U0001f1e9\U0001f1ea",
            "fr": "\U0001f1eb\U0001f1f7",
        }

    async def build_pokemon_table(self):
        async with self.bot.session.get(
            "https://raw.githubusercontent.com/poketwo/data/master/csv/pokemon.csv"
        ) as req:
            raw_csv = await req.text()
            reader = csv.reader(io.StringIO(raw_csv))

            final = {}
            for row in reader:
                ja, ja_r, ja_t, en, de, fr = (
                    row[11],
                    row[12],
                    row[13],
                    row[14],
                    row[16],
                    row[17],
                )

                final[en] = {"ja": ja, "ja_r": ja_r, "ja_t": ja_t, "de": de, "fr": fr}

            assert final["name.en"] == {
                "ja": "name.ja",
                "ja_r": "name.ja_r",
                "ja_t": "name.ja_t",
                "de": "name.de",
                "fr": "name.fr",
            }

            self.pokemon_table = final

    async def cog_load(self) -> None:
        await self.build_pokemon_table()

    def guess(self, hint: str) -> list[str]:
        if not self.pokemon_table:
            raise Exception("Pokémon lookup table not ready yet.")

        guesses: list[str] = [
            p for p in self.pokemon_table.keys() if len(hint) == len(p)
        ]

        for i, letter in enumerate(hint):
            if letter != "_":
                guesses = [p for p in guesses if p[i].lower() == letter.lower()]

        return guesses

    def guess_message(self, message: discord.Message):
        match = HINT_RE.match(message.content)

        if not match:
            if message.embeds:
                embed = message.embeds[0]
                if embed.description and embed.description.startswith(
                    "Guess the pokémon"
                ):
                    raise Exception(
                        "Invoke this command on an `hint` message to get a reasonable guess."
                    )

            raise Exception("No hint found in message.")

        return self.guess(match.group("hint").replace("\\", ""))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def rebuild_table(self, ctx: commands.Context[Estella]):
        """
        Rebuilds internal `PokéTwo` data table.
        """

        msg = await ctx.send("Rebuilding cache...")

        with Timer() as timer:
            await self.build_pokemon_table()

        await msg.edit(content=f"rebuilt cache (took: `{timer():.2}s`)")


async def setup(bot: Estella):
    await bot.add_cog(Hint(bot))
