"""
Kleine Hilfsfunktion, um Aktionen (neuer Eintrag, Bilder hinzugefügt, gelöscht)
in den konfigurierten Log-Channel zu schreiben, falls einer eingerichtet ist.
"""

from typing import Optional

import discord

import database as db


async def log_action(guild: Optional[discord.Guild], embed: discord.Embed) -> None:
    if guild is None:
        return

    channel_id = await db.get_config("log_channel_id")
    if not channel_id:
        return

    channel = guild.get_channel(int(channel_id))
    if not isinstance(channel, discord.TextChannel):
        return

    try:
        await channel.send(embed=embed)
    except discord.HTTPException:
        pass