import logging
from discord.utils import _ColourFormatter  # pyright: ignore[reportPrivateUsage]

logger = logging.getLogger("estella")

handler = logging.StreamHandler()
handler.setFormatter(_ColourFormatter())

logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
