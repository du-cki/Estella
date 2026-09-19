import json
import re
from base64 import b64decode as atob

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from utils import logger

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"


def extract_js_payload(js_text: str, regex_pattern: str):
    match = re.search(regex_pattern, js_text)
    if not match:
        return None

    payload_str = js_text[match.end() :].lstrip()
    if payload_str.startswith("'"):
        str_match = re.match(r"'((?:\\.|[^\\'])*)'", payload_str)
        if str_match:
            return str_match.group(1).replace(r"\'", "'").replace(r"\\", "\\")

        return None

    try:
        data, _ = json.JSONDecoder().raw_decode(payload_str)
        return data
    except json.JSONDecodeError:
        return None


class DDG:
    BASE_URL = atob("aHR0cHM6Ly9kdWNrZHVja2dvLmNvbQ==").decode("utf-8")
    BASE_HTML_URL = atob("aHR0cHM6Ly9odG1sLmR1Y2tkdWNrZ28uY29tL2h0bWwv").decode("utf-8")

    def __init__(self, session: ClientSession):
        self.session = session

    async def parse_embeds(self, html_text: str) -> str | None:
        if payload := extract_js_payload(html_text, r"DDH\.add\(\s*"):  # noqa: SIM102
            if isinstance(payload, dict) and payload.get("from") == "color_codes":
                color = payload.get("data", {})

                return (
                    f"{color.get('hexc', 'Unknown Color')} | "
                    f"RGB: {color.get('rgb')} | "
                    f"HSL: {color.get('hslc')} | "
                    f"CMYB: {color.get('cmyb')} | "
                    f"Complementary: #{color.get('complementary')}"
                )

        if match := re.search(r"nrj\('(/js/spice/currency/[^']+)'", html_text):
            s_url = match.group(1)
            return await self.fetch_currency(s_url)

        return None

    async def fetch_currency(self, s_url: str):
        async with self.session.get(
            f"https://duckduckgo.com{s_url}",
            headers={
                "User-Agent": USER_AGENT,
            },
        ) as resp:
            if resp.status != 200:
                return

            spice_text = await resp.text()

            if data := extract_js_payload(spice_text, r"ddg_spice_currency\(\s*"):  # noqa: SIM102
                if isinstance(data, dict):
                    from_curr = data.get("from", "")
                    amount = data.get("amount", 1.0)

                    to_curr_data = data["to"][0]
                    to_curr = to_curr_data.get("quotecurrency", "")
                    converted = to_curr_data.get("mid", 0.0)

                    rate = converted / amount if amount else 0.0

                    return (
                        f"{amount:g} `{from_curr}` → {converted:.2f} `{to_curr}`\n"
                        f"-# (1 {from_curr} ≈ {rate:.2f} {to_curr})"
                    )

    async def fetch_abstracts(
        self,
        html_text: str,
        headers: dict[str, str],
    ) -> tuple[str, list[dict[str, str]]]:
        vqd = extract_js_payload(html_text, r"vqd\s*[:=]\s*")
        if not vqd:
            raise ValueError("failed to extract vqd")

        d_js_path = extract_js_payload(html_text, r"DDG\.deep\.initialize\(\s*")
        if d_js_path:
            d_js_url = (
                f"https://links.duckduckgo.com{d_js_path}"
                if d_js_path.startswith("/")
                else d_js_path
            )
        else:
            d_js_url = extract_js_payload(
                html_text, r'id=["\']deep_preload_link["\'][^>]*href\s*=\s*'
            )

            if d_js_url:
                d_js_url = d_js_url.replace("&amp;", "&")
            else:
                raise ValueError("failed to extract d.js route")

        headers_ = {
            **headers,
            "Accept": "*/*",
            "Sec-Fetch-Dest": "script",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-site",
        }

        async with self.session.get(
            d_js_url,
            headers=headers_,
        ) as resp:
            d_js_text = await resp.text()

            data = (
                extract_js_payload(
                    d_js_text,
                    r"DDG\.pageLayout\.load\(\s*['\"]d['\"]\s*,",
                )
                or []
            )

            abstracts = []

            for row in data:
                if isinstance(row, dict) and (a := row.get("a")):
                    clean_text = BeautifulSoup(a, "html.parser").get_text(strip=True)
                    abstracts.append({"text": clean_text})

                    if len(abstracts) >= 3:
                        break

        return (vqd, abstracts)

    async def query_qna(
        self,
        query: str,
        vqd: str,
        abstracts: list[dict[str, str]],
    ):
        params = {
            "q": query,
            "vqd": vqd,
        }

        headers = {
            "User-Agent": USER_AGENT,
            "Referer": f"{self.BASE_URL}/?q={query.replace(' ', '+')}",
            "Origin": self.BASE_URL,
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }

        json = {
            "abstracts": abstracts,
        }

        async with self.session.post(
            f"{self.BASE_URL}/qna.js",
            params=params,
            headers=headers,
            json=json,
        ) as response:
            return await response.json()

    async def query(self, query: str) -> str | None:
        try:
            headers = {
                "User-Agent": USER_AGENT,
                "Referer": f"{self.BASE_URL}/",
            }

            async with self.session.get(
                f"{self.BASE_URL}/",
                params={"q": query},
                headers=headers,
            ) as resp:
                html_text = await resp.text()

            if embedded_answer := await self.parse_embeds(html_text):
                return embedded_answer

            vqd, abstracts = await self.fetch_abstracts(html_text, headers)
            resp = await self.query_qna(query, vqd, abstracts)

            if resp.get("action") == "answer" and (answer := resp.get("answer")):
                return answer

        except Exception as err:  # noqa: BLE001
            logger.error("Couldn't parse query for %s:\n%s", query, err)
