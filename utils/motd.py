from mcstatus.motd.components import ParsedMotdComponent, MinecraftColor, Formatting


COLOR_BASE = "\U0000001b[{}m"


def motd_to_ansi(motd: list[ParsedMotdComponent]) -> str:
    final = ""

    for line in motd:
        if isinstance(line, str):
            final += line

        match line:
            case MinecraftColor.BLACK:
                final += COLOR_BASE.format("1;30")
            case MinecraftColor.DARK_BLUE:
                final += COLOR_BASE.format("1;34")
            case MinecraftColor.DARK_GREEN:
                final += COLOR_BASE.format("1;32")
            case MinecraftColor.DARK_AQUA:
                final += COLOR_BASE.format("1;36")
            case MinecraftColor.DARK_RED:
                final += COLOR_BASE.format("1;31")
            case MinecraftColor.DARK_PURPLE:
                final += COLOR_BASE.format("1;35")
            case MinecraftColor.GOLD:
                final += COLOR_BASE.format("1;33")
            case MinecraftColor.GRAY:
                final += COLOR_BASE.format("37")
            case MinecraftColor.DARK_GRAY:
                final += COLOR_BASE.format("1;37")
            case MinecraftColor.BLUE:
                final += COLOR_BASE.format("34")
            case MinecraftColor.GREEN:
                final += COLOR_BASE.format("32")
            case MinecraftColor.AQUA:
                final += COLOR_BASE.format("36")
            case MinecraftColor.RED:
                final += COLOR_BASE.format("31")
            case MinecraftColor.LIGHT_PURPLE:
                final += COLOR_BASE.format("35")
            case MinecraftColor.YELLOW:
                final += COLOR_BASE.format("33")
            case MinecraftColor.WHITE:
                final += COLOR_BASE.format("1;37")
            case MinecraftColor.MINECOIN_GOLD:
                final += COLOR_BASE.format("1;33")
            case Formatting.BOLD:
                final += COLOR_BASE.format("0;1")
            case Formatting.ITALIC:
                final += COLOR_BASE.format("0;3")
            case Formatting.UNDERLINED:
                final += COLOR_BASE.format("0;4")
            case Formatting.STRIKETHROUGH:
                final += COLOR_BASE.format("0;9")
            case Formatting.OBFUSCATED:
                final += COLOR_BASE.format("0;30;46")
            case Formatting.RESET:
                final += COLOR_BASE.format("0")
            case _:
                ...

    return final
