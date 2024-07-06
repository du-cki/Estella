import re

MOTD_RE = re.compile(r"(?:§)([0-9a-fA-FklmnorFKLMNOR])")
MOTD_MAPPING = {
    "f": "0",
    "0": "30",
    "1": "34",
    "2": "32",
    "3": "36",
    "4": "31",
    "5": "35",
    "6": "33",
    "7": "30",
    "8": "30",
    "9": "34",
    "a": "32",
    "b": "34",
    "c": "31",
    "d": "35",
    "e": "33",
}


def motd_map(match: re.Match[str]) -> str:
    code = match.group(1)
    if code == "f":
        return "\x1b[0m"
    
    return f"\x1b[0;1;{MOTD_MAPPING.get(code, '30')}m"


def motd_to_ansi(motd: str) -> str:
    return MOTD_RE.sub(motd_map, motd)
