from __future__ import annotations

import time
import asyncio
import functools
import itertools

from contextlib import contextmanager
from base64 import b64decode
from io import BytesIO

from typing import TYPE_CHECKING, ParamSpec, TypeVar

if TYPE_CHECKING:
    from typing import Generator, Awaitable, Callable, Optional


R = TypeVar("R")
P = ParamSpec("P")


@contextmanager
def Timer():
    start = time.perf_counter()
    yield lambda: end - start
    end = time.perf_counter()


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


def run_in_executor(
    _func: Callable[P, R],
) -> Callable[P, Awaitable[R]]:
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        func = functools.partial(_func, *args, **kwargs)
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(executor=None, func=func)

    return wrapped


def convert_data_uri(data_uri: str) -> tuple[BytesIO, str]:
    header, encoded = data_uri.split(",", 1)
    data = b64decode(encoded)

    mime_type = header.split(";")[0].split(":")[1]
    ext = mime_type.split("/")[1]

    return BytesIO(data), ext


def variants(original: str) -> list[str]:
    return [
        "".join(variant)
        for variant in itertools.product(
            *([char.lower(), char.upper()] for char in original)
        )
    ]
