import os
from discord.utils import MISSING

from typing import TypeVar, Union, overload, Any

T = TypeVar("T")


@overload
def getenv(key: str) -> str: ...


@overload
def getenv(key: str, default: T) -> Union[str, T]: ...


def getenv(key: str, default: Union[Any, T] = MISSING) -> Union[str, T]:
    env = os.getenv(key)
    if env is None:
        if default is MISSING:
            raise RuntimeError(f"`{key}` is not present in the environment variables")

        return default

    return env
