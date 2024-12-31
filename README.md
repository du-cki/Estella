## Estella

A personal discord bot with utilities for my friends.

### Config

Config values marked as `[optional]` can be left as `None`

```py
# config.py
TOKEN = "" # Discord bot token

DEFAULT_PREFIX = "estella" # The default prefix for bot commands, mentioning the bot also works as a prefix.
LOG_FUNNEL_WEBHOOK = None # A discord webhook to funnel all the logs too. [optional]
SERVER_IP = None # a minecraft server to keep track of, for the `server` extension. [optional]
```