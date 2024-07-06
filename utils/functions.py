from typing import Optional


def to_cb(
    code: str,
    *,
    lang: Optional[str] = "",
) -> str:
    return f"```{lang}\n{code}\n```"


def ordinal(n: int) -> str:
    return f"{n}{'tsnrhtdd'[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4]}"
