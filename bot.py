"""
Minecraft Struktur/Biom/Farm-Finder Discord Bot.

Einrichtung siehe README.md.
"""

import os
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import database as db
from logs import log_action
from views import (
    DeleteTypeView,
    EntryView,
    ForumDeleteButton,
    ForumEditButton,
    SearchView,
    _category_emoji,
    _delete_forum_post,
)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Bot-Status ("Spielt ..."/"Schaut ..."/"Hört ..."/"Tritt an in ...") - beliebig
# über die .env-Datei anpassbar, siehe .env.example. Ohne Angabe wird "Spielt
# Minecraft" verwendet.
ACTIVITY_TYPE_MAP = {
    "playing": discord.ActivityType.playing,
    "watching": discord.ActivityType.watching,
    "listening": discord.ActivityType.listening,
    "competing": discord.ActivityType.competing,
}
ACTIVITY_TYPE = os.getenv("BOT_ACTIVITY_TYPE", "playing").strip().lower()
ACTIVITY_NAME = os.getenv("BOT_ACTIVITY_NAME", "Minecraft").strip()

# Online-Status (der farbige Punkt am Bot-Icon) - ebenfalls über die .env
# anpassbar. "offline" zeigt den Bot für andere als offline an (Discord nennt
# das intern "invisible"), der Bot bleibt dabei aber ganz normal online/aktiv.
STATUS_MAP = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "offline": discord.Status.invisible,
    "invisible": discord.Status.invisible,
}
BOT_STATUS = os.getenv("BOT_STATUS", "online").strip().lower()

intents = discord.Intents.default()
intents.message_content = True  # nötig, um hochgeladene Bilder im Eintragen-Channel zu erkennen


class FinderBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await db.init_db()
        # Persistente Views/Buttons registrieren, damit sie auch nach einem
        # Neustart des Bots weiter funktionieren.
        self.add_view(EntryView())
        self.add_view(SearchView())
        self.add_dynamic_items(ForumEditButton, ForumDeleteButton)
        await self.tree.sync()


bot = FinderBot()


@bot.event
async def on_ready() -> None:
    print(f"Eingeloggt als {bot.user} (ID: {bot.user.id})")

    activity_type = ACTIVITY_TYPE_MAP.get(ACTIVITY_TYPE, discord.ActivityType.playing)
    status = STATUS_MAP.get(BOT_STATUS, discord.Status.online)
    activity = discord.Activity(type=activity_type, name=ACTIVITY_NAME) if ACTIVITY_NAME else None
    await bot.change_presence(status=status, activity=activity)


@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx: commands.Context, guild_id: Optional[int] = None) -> None:
    """
    Synchronisiert die Slash-Commands manuell neu.
    Nutzung:
      !sync            -> globale Synchronisierung (kann bis zu 1h dauern, bis Discord es überall anzeigt)
      !sync <guild_id>  -> sofortige Synchronisierung nur für diesen Server (praktisch zum Testen)
    Nur der Bot-Owner darf diesen Command ausführen.
    """
    if guild_id:
        guild = discord.Object(id=guild_id)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        await ctx.send(f"✅ {len(synced)} Slash-Commands für Server `{guild_id}` synchronisiert.")
    else:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ {len(synced)} Slash-Commands global synchronisiert (Discord kann bis zu 1h brauchen).")


@sync.error
async def sync_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.NotOwner):
        await ctx.send("❌ Nur der Bot-Owner darf diesen Command ausführen.")
    else:
        raise error


@bot.tree.command(name="setup_eintragen", description="Richtet diesen Channel als Eintragen-Channel ein (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_eintragen(interaction: discord.Interaction) -> None:
    embed = discord.Embed(
        title="📍 Struktur, Biom oder Farm eintragen",
        description=(
            "Klicke auf den Button, um eine gefundene Struktur, ein Biom oder eine "
            "gebaute Farm mit Name, Koordinaten und optional Bildern einzutragen."
        ),
        color=discord.Color.green(),
    )
    embed.set_footer(text="🏛️ Struktur · 🌳 Biom · 🚜 Farm")
    await interaction.channel.send(embed=embed, view=EntryView())
    await db.set_config("entry_channel_id", str(interaction.channel.id))
    await interaction.response.send_message("✅ Dieser Channel ist jetzt der Eintragen-Channel.", ephemeral=True)


@bot.tree.command(name="setup_suchen", description="Richtet diesen Channel als Suchen-Channel ein (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_suchen(interaction: discord.Interaction) -> None:
    embed = discord.Embed(
        title="🔍 Struktur, Biom oder Farm suchen",
        description=(
            "Klicke auf den Button, um nach einer Struktur, einem Biom oder einer "
            "Farm zu suchen. Gib optional deine aktuelle Position an, um die "
            "Entfernung zur nächsten passenden Fundstelle zu sehen."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="🏛️ Struktur · 🌳 Biom · 🚜 Farm")
    await interaction.channel.send(embed=embed, view=SearchView())
    await db.set_config("search_channel_id", str(interaction.channel.id))
    await interaction.response.send_message("✅ Dieser Channel ist jetzt der Suchen-Channel.", ephemeral=True)


@bot.tree.command(name="setup_log", description="Richtet diesen Channel als Log-Channel ein (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_log(interaction: discord.Interaction) -> None:
    await db.set_config("log_channel_id", str(interaction.channel.id))
    embed = discord.Embed(
        title="📝 Log-Channel eingerichtet",
        description=(
            "Hier werden ab jetzt neue Einträge, hinzugefügte Bilder und Löschungen "
            "protokolliert (mit Name, Kategorie, ID und wer die Aktion ausgeführt hat)."
        ),
        color=discord.Color.greyple(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="📍 Neuer Eintrag · 🖼️ Bilder · 🗑️ Gelöscht")
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ Dieser Channel ist jetzt der Log-Channel.", ephemeral=True)


@bot.tree.command(
    name="setup_farm_forum",
    description="Verknüpft einen Forum-Channel für automatische Farm-Beiträge (Admin)",
)
@app_commands.describe(
    channel="Der Forum-Channel, in dem für neue Farmen automatisch ein Beitrag erstellt werden soll"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_farm_forum(interaction: discord.Interaction, channel: discord.ForumChannel) -> None:
    await db.set_config("farm_forum_channel_id", str(channel.id))
    await interaction.response.send_message(
        f"✅ {channel.mention} ist jetzt verknüpft. Für jede neu eingetragene Farm "
        "wird dort automatisch ein Beitrag mit Koordinaten, Beschreibung und Specs erstellt.",
        ephemeral=True,
    )


@bot.tree.command(
    name="setup_struktur_forum",
    description="Verknüpft einen Forum-Channel für automatische Struktur-Beiträge (Admin)",
)
@app_commands.describe(
    channel="Der Forum-Channel, in dem für neue Strukturen automatisch ein Beitrag erstellt werden soll"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_struktur_forum(interaction: discord.Interaction, channel: discord.ForumChannel) -> None:
    await db.set_config("struktur_forum_channel_id", str(channel.id))
    await interaction.response.send_message(
        f"✅ {channel.mention} ist jetzt verknüpft. Für jede neu eingetragene Struktur "
        "wird dort automatisch ein Beitrag mit Koordinaten, Beschreibung und Tags erstellt.",
        ephemeral=True,
    )


@bot.tree.command(
    name="setup_biom_forum",
    description="Verknüpft einen Forum-Channel für automatische Biom-Beiträge (Admin)",
)
@app_commands.describe(
    channel="Der Forum-Channel, in dem für neue Biome automatisch ein Beitrag erstellt werden soll"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_biom_forum(interaction: discord.Interaction, channel: discord.ForumChannel) -> None:
    await db.set_config("biom_forum_channel_id", str(channel.id))
    await interaction.response.send_message(
        f"✅ {channel.mention} ist jetzt verknüpft. Für jedes neu eingetragene Biom "
        "wird dort automatisch ein Beitrag mit Koordinaten, Beschreibung und Tags erstellt.",
        ephemeral=True,
    )


@bot.tree.command(
    name="eintrag_loeschen",
    description="Löscht einen Eintrag - per ID direkt oder interaktiv per Suche/Durchklicken (Admin)",
)
@app_commands.describe(
    eintrag_id="Optional: direkt per ID löschen (steht in der Sucher-Ansicht bzw. Eintragsbestätigung). "
    "Weglassen, um stattdessen per Suche/Durchklicken zu löschen."
)
@app_commands.checks.has_permissions(administrator=True)
async def eintrag_loeschen(interaction: discord.Interaction, eintrag_id: Optional[int] = None) -> None:
    if eintrag_id is not None:
        entry = await db.get_entry(eintrag_id)
        deleted = await db.delete_entry(eintrag_id)
        if deleted:
            await interaction.response.send_message(f"🗑️ Eintrag {eintrag_id} wurde gelöscht.", ephemeral=True)
            if entry:
                await _delete_forum_post(interaction.guild, entry.get("forum_thread_id"))
                await log_action(
                    interaction.guild,
                    discord.Embed(
                        title="🗑️ Eintrag gelöscht",
                        description=(
                            f"{_category_emoji(entry['typ'])} **{entry['name']}** ({entry['typ']}) "
                            f"ID `{entry['id']}`\nGelöscht von: {interaction.user.mention}"
                        ),
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow(),
                    ),
                )
        else:
            await interaction.response.send_message(f"❌ Eintrag {eintrag_id} wurde nicht gefunden.", ephemeral=True)
        return

    await interaction.response.send_message(
        "Welchen Eintrag möchtest du löschen? Wähle zunächst eine Kategorie:",
        view=DeleteTypeView(),
        ephemeral=True,
    )


@setup_eintragen.error
@setup_suchen.error
@setup_log.error
@setup_farm_forum.error
@setup_struktur_forum.error
@setup_biom_forum.error
@eintrag_loeschen.error
async def admin_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ Dafür brauchst du Administrator-Rechte auf diesem Server.", ephemeral=True
        )
    else:
        raise error


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Kein DISCORD_TOKEN gefunden. Bitte .env Datei anlegen (siehe .env.example).")
    bot.run(TOKEN)