from __future__ import annotations

import discord
from discord.ext import commands
from discord import ui, app_commands

from io import BytesIO

from libs.dictcc import DictCC, word_autocomplete_for

from utils import generate_waveform_from_audio
from utils.views import BaseView

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Self

    from utils import Estella

    Interaction = discord.Interaction[Estella]


GERMAN_RED = 0xFF0000
SWEDISH_YELLOW = 0xFFCD00


class DefinitionView(BaseView):
    def __init__(self, audio_url: str, btn_label: str, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.audio_url = audio_url

        self.btn: ui.Button[Self] = ui.Button(label=btn_label)
        self.btn.callback = self.pronounciation
        self.add_item(self.btn)

    async def pronounciation(self, interaction: Interaction):
        assert interaction.channel
        
        self.btn.disabled = True
        await interaction.response.edit_message(view=self)
        
        message = await interaction.original_response()

        async with interaction.client.session.get(self.audio_url) as req:
            if req.content_type != "audio/mpeg":
                return await message.reply(
                    "I couldn't find any audio recording for this word."
                )

            audio = BytesIO(await req.read())

            file = discord.File(audio, filename="pronounciation.mp3")
            waveform, duration_secs = await generate_waveform_from_audio(file.fp.read())
            file.reset()

            await interaction.client.send_voice_message(
                interaction.channel.id,
                file,
                waveform=waveform,
                duration_secs=duration_secs,
                reference=message,
            )


class Dictionary(commands.Cog):
    def __init__(self, bot: Estella):
        self.bot = bot

        self.dictcc = DictCC(session=bot.session)
        self.SECTION_LIMIT = 3
        self.IGNORED_SECTIONS = [
            "Substantive",
        ]

    async def _handle_dictionary_query(
        self,
        interaction: Interaction,
        *,
        word: str,
        _from: str,
        _to: str,
        colour: int,
        btn_label: str,
        reversed: bool = False,
    ):
        definition = await self.dictcc.define(word, _from=_from, _to=_to)
        if not definition:
            return await interaction.response.send_message(
                f"I couldn't find any translations for {word!r}."
            )

        sections = 0
        builder = ""
        for seg_name, seg_value in definition.items():
            if sections == self.SECTION_LIMIT:  # we don't want to bloat our embed.
                break

            if seg_name in self.IGNORED_SECTIONS:
                continue

            sections += 1

            if seg_name != "Definition":
                builder += f"\n### {seg_name}\n"

            for node in seg_value[:3]:
                if reversed:
                    _from_lang, _to_lang = node
                else:
                    _to_lang, _from_lang = node

                if seg_name == "Definition":
                    builder += f"{_to_lang.word}; "
                else:
                    builder += f"\n- {_from_lang.word} [{_to_lang.word}]"

        if reversed:
            first_definition, _ = definition["Definition"][0]
        else:
            _, first_definition = definition["Definition"][0]

        embed = discord.Embed(
            title=first_definition.word,
            description=builder,
            colour=colour,
        )

        await interaction.response.send_message(
            embed=embed,
            view=DefinitionView(
                first_definition.audio,
                btn_label=btn_label,
                author_id=interaction.user.id,
            ),
        )

    @app_commands.command(
        description="Gibt die englische Bedeutung eines deutschen Wortes."
    )
    @app_commands.autocomplete(
        wort=word_autocomplete_for(_from="de", _to="en", lang_id=1, lang_dir=1)
    )
    @app_commands.describe(wort="Das Wort zum Übersetzen.")
    async def worterbuch(
        self,
        interaction: Interaction,
        wort: str,
    ):
        await self._handle_dictionary_query(
            interaction,
            word=wort,
            _from="de",
            _to="en",
            colour=GERMAN_RED,
            btn_label="Aussprache",
        )

    @app_commands.command(description="Ger den engelska betydelsen på ett svenskt ord.")
    @app_commands.autocomplete(
        ord=word_autocomplete_for(_from="sv", _to="en", lang_id=10, lang_dir=3)
    )
    @app_commands.describe(ord="Ordet att översätta.")
    async def ordbok(
        self,
        interaction: Interaction,
        ord: str,
    ):
        await self._handle_dictionary_query(
            interaction,
            word=ord,
            _from="en",
            _to="sv",
            colour=SWEDISH_YELLOW,
            btn_label="Uttal",
            reversed=True,
        )


async def setup(bot: Estella):
    await bot.add_cog(Dictionary(bot))
