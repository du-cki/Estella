from mcstatus.motd.components import ParsedMotdComponent, MinecraftColor, Formatting

COLOR_BASE = "\U0000001b[{}m"


def match_color_to_str(color: ParsedMotdComponent) -> str:
    match color:
        case MinecraftColor.BLACK:
            return COLOR_BASE.format("1;30")
        case MinecraftColor.DARK_BLUE:
            return COLOR_BASE.format("1;34")
        case MinecraftColor.DARK_GREEN:
            return COLOR_BASE.format("1;32")
        case MinecraftColor.DARK_AQUA:
            return COLOR_BASE.format("1;36")
        case MinecraftColor.DARK_RED:
            return COLOR_BASE.format("1;31")
        case MinecraftColor.DARK_PURPLE:
            return COLOR_BASE.format("1;35")
        case MinecraftColor.GOLD:
            return COLOR_BASE.format("1;33")
        case MinecraftColor.GRAY:
            return COLOR_BASE.format("37")
        case MinecraftColor.DARK_GRAY:
            return COLOR_BASE.format("1;37")
        case MinecraftColor.BLUE:
            return COLOR_BASE.format("34")
        case MinecraftColor.GREEN:
            return COLOR_BASE.format("32")
        case MinecraftColor.AQUA:
            return COLOR_BASE.format("36")
        case MinecraftColor.RED:
            return COLOR_BASE.format("31")
        case MinecraftColor.LIGHT_PURPLE:
            return COLOR_BASE.format("35")
        case MinecraftColor.YELLOW:
            return COLOR_BASE.format("33")
        case MinecraftColor.WHITE:
            return COLOR_BASE.format("1;37")
        case MinecraftColor.MINECOIN_GOLD:
            return COLOR_BASE.format("1;33")
        case Formatting.BOLD:
            return COLOR_BASE.format("0;1")
        case Formatting.ITALIC:
            return COLOR_BASE.format("0;3")
        case Formatting.UNDERLINED:
            return COLOR_BASE.format("0;4")
        case Formatting.STRIKETHROUGH:
            return COLOR_BASE.format("0;9")
        case Formatting.OBFUSCATED:
            return COLOR_BASE.format("0;30;46")
        case Formatting.RESET:
            return COLOR_BASE.format("0")
        case _:
            return COLOR_BASE.format("0")  # if we don't know what it is, just reset it


def motd_to_ansi(motd: list[ParsedMotdComponent]) -> str:
    final = ""

    for line in motd:
        if isinstance(line, str):
            final += line

        final += match_color_to_str(line)

    return final
