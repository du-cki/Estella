from typing import Optional, Generator


def to_cb(
    code: str,
    *,
    lang: Optional[str] = "",
) -> str:
    return f"```{lang}\n{code}\n```"


def ordinal(n: int) -> str:
    return f"{n}{'tsnrhtdd'[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4]}"


def as_chunks(
    n: int,
    text: str,
) -> Generator[str, None, None]:
    for i in range(0, len(text), n):
        yield text[i : i + n]
