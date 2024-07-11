from mcstatus.motd.components import (
    ParsedMotdComponent,
    MinecraftColor,
    Formatting,
)

COLOR_BASE = "\U0000001b[{}m"

COLOR_MAP: dict[ParsedMotdComponent, str] = {
    MinecraftColor.BLACK: COLOR_BASE.format("1;30"),
    MinecraftColor.DARK_BLUE: COLOR_BASE.format("1;34"),
    MinecraftColor.DARK_GREEN: COLOR_BASE.format("1;32"),
    MinecraftColor.DARK_AQUA: COLOR_BASE.format("1;36"),
    MinecraftColor.DARK_RED: COLOR_BASE.format("1;31"),
    MinecraftColor.DARK_PURPLE: COLOR_BASE.format("1;35"),
    MinecraftColor.GOLD: COLOR_BASE.format("1;33"),
    MinecraftColor.GRAY: COLOR_BASE.format("37"),
    MinecraftColor.DARK_GRAY: COLOR_BASE.format("1;37"),
    MinecraftColor.BLUE: COLOR_BASE.format("34"),
    MinecraftColor.GREEN: COLOR_BASE.format("32"),
    MinecraftColor.AQUA: COLOR_BASE.format("36"),
    MinecraftColor.RED: COLOR_BASE.format("31"),
    MinecraftColor.LIGHT_PURPLE: COLOR_BASE.format("35"),
    MinecraftColor.YELLOW: COLOR_BASE.format("33"),
    MinecraftColor.WHITE: COLOR_BASE.format("1;37"),
    MinecraftColor.MINECOIN_GOLD: COLOR_BASE.format("1;33"),
    Formatting.BOLD: COLOR_BASE.format("0;1"),
    Formatting.ITALIC: COLOR_BASE.format("0;3"),
    Formatting.UNDERLINED: COLOR_BASE.format("0;4"),
    Formatting.STRIKETHROUGH: COLOR_BASE.format("0;9"),
    Formatting.OBFUSCATED: COLOR_BASE.format("0;30;46"),
    Formatting.RESET: COLOR_BASE.format("0"),
}


def motd_to_ansi(motd: list[ParsedMotdComponent]) -> str:
    return "".join(
        component
        if isinstance(component, str)
        else COLOR_MAP.get(component, COLOR_BASE.format("0"))
        for component in motd
    )
