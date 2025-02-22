from __future__ import annotations

import re

from discord import app_commands
from urllib.parse import quote_plus, urlencode

from bs4 import BeautifulSoup, Tag
from collections import defaultdict

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from typing import Any, Self

    from discord import Interaction
    from aiohttp import ClientSession

    from utils import Estella
    from ext.dictionary import Dictionary


def word_autocomplete_for(*, _from: str, _to: str, lang_id: int, lang_dir: int):
    async def inner(
        interaction: Interaction["Estella"],
        current: str,
    ) -> list[app_commands.Choice[str]]:
        dict_cog: Dictionary = interaction.client.cogs[
            "Dictionary"
        ]  # pyright: ignore[reportAssignmentType]

        cls = dict_cog.dictcc
        search = await cls.search(
            current,
            lang=f"{_from}{_to}",
            lang_id=lang_id,
            lang_dir=lang_dir,
        )

        return [
            app_commands.Choice(
                name=word,
                value=word,
            )
            for word in search
        ][:25]

    return inner


class Node(NamedTuple):
    word: str
    lang: str
    audio: str

    @classmethod
    def from_tag(
        cls,
        tag: Tag,
        *,
        lang: str,
        lp: str,
        audio_id: str,
    ) -> Self:
        word = " ".join(word.get_text() for word in tag.select("a:not(:has(kbd))"))

        url = Route(
            "GET",
            "/speak.audio.v2.php",
            query={
                "id": audio_id,
                "lp": lp,
                "lang": f"{lang}_rec_ip",
                "error_as_text": 1,
                "type": "mp3",
            },
            lang="audio",
        ).url

        return cls(
            word=word,
            lang=lang,
            audio=url,
        )


class Route:
    BASE = "https://{lang}.dict.cc"

    def __init__(
        self,
        method: str,
        path: str,
        *,
        lang: str,
        query: dict[str, Any],
    ):
        self.method = method
        self.path = path
        self.lang = lang

        self.query = query

    @property
    def url(self):
        url = f"{self.BASE}{self.path}".format_map({"lang": self.lang})
        if self.query:
            url += f"?{urlencode(self.query)}"

        return url

    def __repr__(self):
        return f"<Route method={self.method!r} url={self.url!r}>"



class DictCC:
    ID_ARRAY = re.compile(r"var idArr = new Array\(((?:(?:\w+),?)+)\);")

    def __init__(self, *, session: ClientSession):
        self._session = session

    async def request(self, route: Route) -> str:
        async with self._session.request(route.method, route.url) as req:
            if req.status != 200:
                raise Exception(
                    f"Recieved an {req.status} status code while querying: {route.url}"
                )

            return await req.text()

    async def define(
        self,
        word: str,
        *,
        _from: str,
        _to: str,
    ):
        resp = await self.request(
            Route(
                "GET",
                "/",
                query={"s": word},
                lang=f"{_from}{_to}",
            )
        )

        if "no translations found" in resp:
            return None

        soup = BeautifulSoup(resp, features="html.parser")

        audio_ids: list[str] = []
        script_tag = soup.select("table + script[type='text/javascript']")
        if script_tag:
            js = script_tag[0].get_text()

            m = self.ID_ARRAY.search(js)
            if m:
                ids, *_ = m.groups()
                audio_ids = ids.split(",")

        # first section will always contain the definitons
        current_section = "Definition"
        sections: dict[str, list[tuple[Node, Node]]] = defaultdict(list)

        tables = soup.find_all("table")

        word_table = tables[2]
        assert isinstance(word_table, Tag)  # type-checking

        rows = word_table.select("tr")

        for row in rows:
            heading = row.find("td", attrs={"colspan": "4"})
            if heading:
                current_section = heading.get_text()
                continue

            is_valid_def = row.select("td[class='td7cml']")

            if is_valid_def:
                row_id = int(str(row["id"]).removeprefix("tr"))
                lhs_lang_tag, rhs_lang_tag = row.select("td[class='td7nl']")

                lhs_lang = Node.from_tag(
                    lhs_lang_tag,
                    lang=_to,
                    audio_id=audio_ids[row_id],
                    lp=f"{_from}{_to}",
                )

                rhs_lang = Node.from_tag(
                    rhs_lang_tag,
                    lang=_from,
                    audio_id=audio_ids[row_id],
                    lp=f"{_from}{_to}",
                )

                sections[current_section].append((lhs_lang, rhs_lang))

        return sections

    async def search(
        self,
        word: str,
        *,
        lang: str,
        lang_id: int,
        lang_dir: int,
        limit: int = 25,
    ) -> list[str]:
        if len(word) < 2:
            return []

        resp = await self.request(
            Route(
                "GET",
                "/inc/ajax_autosuggest.php",
                query={
                    "s": quote_plus(word),
                    "lp_id": lang_id,
                    "ldir": lang_dir,
                    "nr": limit,
                    "jsonp": 0,
                    "infl": 1,
                    "check_typo": 1,
                    "use_mt": 1,
                },
                lang=lang,
            )
        )

        pairs = [line.split() for line in resp.splitlines()]

        # since we're already filtering the lang id in the request, we don't have to worry about
        # the lang_id here amd disregard it entirely.
        return [word for (word, *_lang_id) in pairs]

