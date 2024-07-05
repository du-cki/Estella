from typing import Optional


def to_cb(code: str, *, lang: Optional[str] = "") -> str:
    return f"```{lang}\n{code}\n```"
