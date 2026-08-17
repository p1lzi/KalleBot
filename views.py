"""
UI-Komponenten: Buttons, dreistufige Auswahl (Struktur / Biom / Farm), paginierte und
durchsuchbare Dropdowns, Modals und die Ergebnis-Ansichten für Suche und Löschen.

Ablauf Eintragen:  Button -> Dropdown (Struktur, Biom oder Farm?) -> Dropdown (konkreter
                   Eintrag, ggf. über mehrere Seiten mit Pfeil-Buttons und einem
                   Such-Button zum Filtern) -> Modal (Name, Koordinaten, Beschreibung,
                   bei Farmen zusätzlich Specs) -> ephemere Bestätigung -> optional Tags
                   (vorgeschlagen: Overworld/Nether/End, plus eigene Tags, bei jeder
                   Kategorie) -> bei Farmen zusätzlich ein YouTube-Tutorial-Link -> bei
                   jeder Kategorie optional eine individuelle Embed-Farbe -> Bilder
                   werden im Channel gesendet, vom Bot gruppiert in einen versteckten
                   Archiv-Channel kopiert (damit die Links dauerhaft gültig bleiben) und
                   erst danach (nach Klick auf "✅ Fertig" oder Timeout) werden die
                   ursprünglichen Nachrichten gelöscht. Über "📝 Bilder beschreiben" kann
                   man den Bildern noch Beschreibungen hinzufügen. Ist für die jeweilige
                   Kategorie ein Forum-Channel verknüpft (/setup_struktur_forum,
                   /setup_biom_forum, /setup_farm_forum), wird zusätzlich automatisch
                   ein Forum-Beitrag mit den Tags als echte Discord-Forum-Tags erstellt.

Ablauf Suchen:     Button -> Dropdown (Struktur, Biom oder Farm?) -> Dropdown (konkreter
                   Eintrag oder "Alle", nur Kategorien mit vorhandenen Einträgen, ggf.
                   paginiert/durchsuchbar) -> Modal (Suchbegriff optional, eigene Position
                   optional) -> ephemere Ergebnisliste mit Zurück/Weiter. Bilder und
                   Farm-Specs sind standardmäßig eingeklappt und lassen sich per Button
                   einblenden; über "📏 Entfernung berechnen" kann die Distanz auch
                   nachträglich berechnet werden.

Ablauf Löschen:    Wie Suchen (ohne Entfernungs-Button), aber mit einem zusätzlichen
                   Lösch-Button pro Ergebnis.
"""

import asyncio
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import discord
from discord import ui

import database as db
from logs import log_action

# Discord erlaubt maximal 10 Embeds pro Nachricht - einer davon ist für die Infobox
# reserviert, der Rest steht für Bilder zur Verfügung (kein künstliches Zusatzlimit).
MAX_IMAGE_EMBEDS = 9

# Listen, aus denen im zweiten Schritt per Dropdown ausgewählt werden kann.
# Format: (Anzeigename, Emoji). Bei Bedarf hier einfach anpassen/erweitern -
# auch mehr als 25 Einträge sind kein Problem, dann wird automatisch mit
# Pfeil-Buttons geblättert bzw. kann über den Such-Button gefiltert werden.
STRUCTURES: List[Tuple[str, str]] = [
    ("Village", "🏘️"),
    ("Stronghold", "🏰"),
    ("Nether Fortress", "🔥"),
    ("Bastion Remnant", "🐗"),
    ("Ocean Monument", "🌊"),
    ("Ocean Ruins", "🪸"),
    ("Shipwreck", "🚢"),
    ("Buried Treasure", "💰"),
    ("Jungle Pyramid", "🌴"),
    ("Desert Pyramid", "🏜️"),
    ("Desert Well", "🪣"),
    ("Swamp Hut", "🧙"),
    ("Woodland Mansion", "🏚️"),
    ("Pillager Outpost", "🏹"),
    ("Mineshaft", "⛏️"),
    ("End City", "🌌"),
    ("End Gateway", "🌀"),
    ("Igloo", "❄️"),
    ("Ruined Portal", "🟪"),
    ("Ancient City", "💀"),
    ("Trail Ruins", "🏺"),
    ("Trial Chambers", "⚔️"),
    ("Nether Fossil", "🦴"),
    ("Other Structure", "❓"),
]

BIOMES: List[Tuple[str, str]] = [
    # Ebenen / Wälder / Taiga / Savanne / Wüste / Dschungel
    ("Plains", "🌾"),
    ("Sunflower Plains", "🌻"),
    ("Forest", "🌲"),
    ("Flower Forest", "🌸"),
    ("Birch Forest", "🌳"),
    ("Old Growth Birch Forest", "🌳"),
    ("Dark Forest", "🌑"),
    ("Taiga", "🌲"),
    ("Snowy Taiga", "❄️"),
    ("Old Growth Pine Taiga", "🌲"),
    ("Old Growth Spruce Taiga", "🌲"),
    ("Savanna", "🦒"),
    ("Savanna Plateau", "🦒"),
    ("Windswept Savanna", "🌬️"),
    ("Desert", "🏜️"),
    ("Badlands", "🟧"),
    ("Eroded Badlands", "🟧"),
    ("Wooded Badlands", "🌵"),
    ("Jungle", "🌴"),
    ("Sparse Jungle", "🌴"),
    ("Bamboo Jungle", "🎋"),
    ("Swamp", "🐸"),
    ("Mangrove Swamp", "🌿"),
    ("Mushroom Fields", "🍄"),
    ("Snowy Plains", "❄️"),
    # Berge / Gebirge / Kälte
    ("Ice Spikes", "🧊"),
    ("Windswept Hills", "⛰️"),
    ("Windswept Gravelly Hills", "⛰️"),
    ("Windswept Forest", "🌬️"),
    ("Meadow", "🌼"),
    ("Cherry Grove", "🌸"),
    ("Grove", "🌲"),
    ("Snowy Slopes", "🏔️"),
    ("Frozen Peaks", "🏔️"),
    ("Jagged Peaks", "🏔️"),
    ("Stony Peaks", "🪨"),
    # Flüsse / Strände / Höhlen / Ozeane
    ("River", "🏞️"),
    ("Frozen River", "❄️"),
    ("Beach", "🏖️"),
    ("Snowy Beach", "❄️"),
    ("Stony Shore", "🪨"),
    ("Dripstone Caves", "🪨"),
    ("Lush Caves", "🌿"),
    ("Deep Dark", "🕳️"),
    ("Ocean", "🌊"),
    ("Deep Ocean", "🌊"),
    ("Warm Ocean", "🌊"),
    ("Lukewarm Ocean", "🌊"),
    ("Deep Lukewarm Ocean", "🌊"),
    ("Cold Ocean", "🌊"),
    ("Deep Cold Ocean", "🌊"),
    ("Frozen Ocean", "🧊"),
    ("Deep Frozen Ocean", "🧊"),
    # Nether
    ("Nether Wastes", "🔥"),
    ("Crimson Forest", "🟥"),
    ("Warped Forest", "🟦"),
    ("Soul Sand Valley", "👻"),
    ("Basalt Deltas", "🌋"),
    # End
    ("The End", "🌌"),
    ("Small End Islands", "🌌"),
    ("End Midlands", "🌌"),
    ("End Highlands", "🌌"),
    ("End Barrens", "🌌"),
    ("Other Biome", "❓"),
]

FARMS: List[Tuple[str, str]] = [
    ("Iron Farm", "🔩"),
    ("Gold Farm", "🪙"),
    ("Wither Skeleton Farm", "💀"),
    ("Enderman Farm", "👁️"),
    ("General Mob Farm", "🧟"),
    ("XP Farm", "⭐"),
    ("Raid Farm", "🏳️"),
    ("Guardian Farm", "🔱"),
    ("Slime Farm", "🟢"),
    ("Crop Farm", "🌾"),
    ("Sugar Cane Farm", "🎋"),
    ("Bamboo Farm", "🎍"),
    ("Cactus Farm", "🌵"),
    ("Melon/Pumpkin Farm", "🎃"),
    ("Tree Farm", "🌳"),
    ("Villager Breeder", "👨‍🌾"),
    ("Bee/Honey Farm", "🐝"),
    ("Snow Farm", "❄️"),
    ("Ice Farm", "🧊"),
    ("Kelp Farm", "🌿"),
    ("Blaze Farm", "🔥"),
    ("Ghast Farm", "👻"),
    ("Copper Farm", "🟠"),
    ("Fish Farm", "🐟"),
    ("Stone/Cobblestone Generator", "⛏️"),
    ("Other Farm", "❓"),
]

BASES: List[Tuple[str, str]] = [
    ("Hauptbase", "🏠"),
    ("Nebenbase", "🏡"),
    ("Community-Base", "🏘️"),
    ("Shop", "🏪"),
    ("Redstone-Werkstatt", "⚙️"),
    ("Lager/Sortiersystem", "📦"),
    ("Bahnhof/Transport-Hub", "🚉"),
    ("Aussichtsturm", "🗼"),
    ("Sonstige Base", "❓"),
]

# Zuordnung von Kategorie-Namen zu Emoji/Farbe für hübschere Embeds.
_STRUCTURE_LABELS = {label for label, _ in STRUCTURES}
_BIOME_LABELS = {label for label, _ in BIOMES}
_FARM_LABELS = {label for label, _ in FARMS}
_BASE_LABELS = {label for label, _ in BASES}
_CATEGORY_EMOJI: Dict[str, str] = {
    label: emoji for label, emoji in STRUCTURES + BIOMES + FARMS + BASES
}


def _category_emoji(category: str) -> str:
    return _CATEGORY_EMOJI.get(category, "📍")


def _category_color(category: str) -> discord.Color:
    if category in _STRUCTURE_LABELS:
        return discord.Color.blue()
    if category in _BIOME_LABELS:
        return discord.Color.green()
    if category in _FARM_LABELS:
        return discord.Color.gold()
    if category in _BASE_LABELS:
        return discord.Color.purple()
    return discord.Color.blurple()


def _resolve_color(category: str, custom_hex: Optional[str]) -> discord.Color:
    """Nutzt die individuell für den Eintrag festgelegte Farbe, falls vorhanden,
    sonst die Standardfarbe je Kategorie (blau/grün/gold/lila)."""
    if custom_hex:
        try:
            return discord.Color(int(custom_hex.lstrip("#"), 16))
        except ValueError:
            pass
    return _category_color(category)


# Konfiguration je nach Oberkategorie (Struktur/Biom/Farm/Base): Liste, Anzeigetext, "Alle"-Label.
_GROUPS: Dict[str, Tuple[List[Tuple[str, str]], str, str]] = {
    "struktur": (STRUCTURES, "Wähle jetzt die Struktur aus:", "Alle Strukturen"),
    "biom": (BIOMES, "Wähle jetzt das Biom aus:", "Alle Biome"),
    "farm": (FARMS, "Wähle jetzt die Farm aus:", "Alle Farmen"),
    "base": (BASES, "Wähle jetzt die Base aus:", "Alle Basen"),
}


async def _get_image_channel(guild: discord.Guild) -> discord.TextChannel:
    """
    Liefert den versteckten Channel, in den Bilder dauerhaft kopiert werden
    (damit die Links auch nach dem Löschen der ursprünglichen Nachricht gültig
    bleiben). Wird beim ersten Bild-Upload automatisch angelegt und ist nur für
    den Bot sichtbar.
    """
    channel_id = await db.get_config("image_channel_id")
    if channel_id:
        channel = guild.get_channel(int(channel_id))
        if isinstance(channel, discord.TextChannel):
            return channel

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
    }
    channel = await guild.create_text_channel(
        "bild-archiv", overwrites=overwrites, reason="Bild-Speicher für den Struktur/Biom/Farm-Finder-Bot"
    )
    await db.set_config("image_channel_id", str(channel.id))
    return channel


async def _resolve_forum_tags(channel: discord.ForumChannel, tag_names: List[str]) -> List[discord.ForumTag]:
    """
    Findet zu den übergebenen Tag-Namen passende, bereits am Forum-Channel
    vorhandene Tags (Discord-native Forum-Tags, damit man im Forum danach
    filtern/suchen kann). Fehlende Tags werden - sofern noch Platz ist (max.
    20 Tags pro Forum-Channel) - automatisch am Channel angelegt.
    """
    tag_names = [t.strip() for t in tag_names if t.strip()]
    if not tag_names:
        return []

    existing = {t.name.lower(): t for t in channel.available_tags}
    resolved: List[discord.ForumTag] = []
    missing: List[str] = []

    for name in tag_names:
        tag = existing.get(name.lower())
        if tag:
            resolved.append(tag)
        else:
            missing.append(name)

    if missing:
        room = 20 - len(channel.available_tags)
        to_create = missing[: max(0, room)]
        if to_create:
            try:
                new_tag_list = list(channel.available_tags) + [
                    discord.ForumTag(name=n[:20]) for n in to_create
                ]
                updated_channel = await channel.edit(available_tags=new_tag_list)
                existing_after = {t.name.lower(): t for t in updated_channel.available_tags}
                for n in to_create:
                    tag = existing_after.get(n[:20].lower())
                    if tag:
                        resolved.append(tag)
            except discord.HTTPException:
                pass

    # Discord erlaubt maximal 5 angewendete Tags pro Forum-Beitrag.
    return resolved[:5]


async def _apply_forum_tags(thread: discord.Thread, tags_str: Optional[str]) -> None:
    """Setzt die Discord-Forum-Tags eines bestehenden Beitrags neu (z.B. nach
    nachträglicher Änderung der Tags)."""
    channel = thread.parent
    if not isinstance(channel, discord.ForumChannel):
        return
    tag_names = (tags_str or "").split(",")
    applied_tags = await _resolve_forum_tags(channel, tag_names)
    try:
        await thread.edit(applied_tags=applied_tags)
    except discord.HTTPException:
        pass


def _forum_config_key(category: str) -> Optional[str]:
    """Liefert den Config-Key des passenden Forum-Channels für die Kategorie
    (jede Oberkategorie - Struktur/Biom/Farm/Base - kann einen eigenen Forum-Channel
    haben)."""
    if category in _STRUCTURE_LABELS:
        return "struktur_forum_channel_id"
    if category in _BIOME_LABELS:
        return "biom_forum_channel_id"
    if category in _FARM_LABELS:
        return "farm_forum_channel_id"
    if category in _BASE_LABELS:
        return "base_forum_channel_id"
    return None


async def _create_forum_post(
    guild: Optional[discord.Guild],
    entry_id: int,
    name: str,
    category: str,
    embeds: List[discord.Embed],
    tags: Optional[str] = None,
) -> None:
    """
    Erstellt automatisch einen Forum-Beitrag für einen neuen Eintrag, falls für
    dessen Kategorie (Struktur/Biom/Farm) per /setup_struktur_forum,
    /setup_biom_forum bzw. /setup_farm_forum ein Forum-Channel verknüpft wurde.
    Ohne Verknüpfung passiert nichts - kein Fehler, einfach nur kein Beitrag.
    Vorhandene Tags werden dabei als echte Discord-Forum-Tags angewendet, damit
    man später im Forum danach filtern/suchen kann. Der Beitrag bekommt
    außerdem "✏️ Bearbeiten"/"🗑️ Löschen"-Buttons.
    """
    if guild is None:
        return

    config_key = _forum_config_key(category)
    if config_key is None:
        return

    channel_id = await db.get_config(config_key)
    if not channel_id:
        return

    channel = guild.get_channel(int(channel_id))
    if not isinstance(channel, discord.ForumChannel):
        return

    applied_tags = await _resolve_forum_tags(channel, (tags or "").split(","))

    view = discord.ui.View(timeout=None)
    view.add_item(ForumEditButton(entry_id))
    view.add_item(ForumDeleteButton(entry_id))

    try:
        result = await channel.create_thread(
            name=name[:100], embeds=embeds, applied_tags=applied_tags, view=view
        )
        await db.set_forum_thread(entry_id, result.thread.id)
    except discord.HTTPException:
        pass


async def _get_forum_thread(guild: Optional[discord.Guild], thread_id: Optional[int]) -> Optional[discord.Thread]:
    if guild is None or not thread_id:
        return None
    try:
        thread = guild.get_channel_or_thread(thread_id)
        if thread is None:
            thread = await guild.fetch_channel(thread_id)
        return thread if isinstance(thread, discord.Thread) else None
    except discord.HTTPException:
        return None


async def _sync_forum_post(guild: Optional[discord.Guild], entry_id: int) -> None:
    """
    Aktualisiert den bestehenden Forum-Beitrag eines Eintrags neu (z.B. nachdem
    eine Bildbeschreibung oder ein Tag nachträglich gesetzt wurde), damit der
    Beitrag im Forum immer dem aktuellen Stand entspricht.
    """
    entry = await db.get_entry(entry_id)
    if not entry or not entry.get("forum_thread_id"):
        return

    thread = await _get_forum_thread(guild, entry["forum_thread_id"])
    if thread is None:
        return

    images = await db.get_images_full(entry_id)
    embeds = _build_forum_embeds(
        name=entry["name"],
        category=entry["typ"],
        coord_str=_format_coords(entry),
        beschreibung=entry.get("beschreibung"),
        specs=entry.get("specs"),
        tags=entry.get("tags"),
        youtube_link=entry.get("youtube_link"),
        custom_color=entry.get("color"),
        creator=entry.get("ersteller_name") or "Unbekannt",
        entry_id=entry_id,
        images=images,
    )
    try:
        starter_message = await thread.fetch_message(thread.id)
        await starter_message.edit(embeds=embeds)
        if thread.name != entry["name"][:100]:
            await thread.edit(name=entry["name"][:100])
    except discord.HTTPException:
        pass

    await _apply_forum_tags(thread, entry.get("tags"))


async def _delete_forum_post(guild: Optional[discord.Guild], thread_id: Optional[int]) -> None:
    """Löscht den zu einem Eintrag gehörenden Forum-Beitrag, falls vorhanden."""
    thread = await _get_forum_thread(guild, thread_id)
    if thread is None:
        return
    try:
        await thread.delete()
    except discord.HTTPException:
        pass


def _format_coords(entry: Dict[str, Any]) -> str:
    if entry.get("y") is not None:
        return f"X: {entry['x']} | Y: {entry['y']} | Z: {entry['z']}"
    return f"X: {entry['x']} | Z: {entry['z']}"


def _format_coords_input(entry: Dict[str, Any]) -> str:
    """Wie _format_coords, aber als reine Zahlen zum Vorausfüllen des Formulars."""
    if entry.get("y") is not None:
        return f"{entry['x']} {entry['y']} {entry['z']}"
    return f"{entry['x']} {entry['z']}"


async def _can_edit_or_delete(interaction: discord.Interaction, entry: Dict[str, Any]) -> bool:
    """Nur die ursprüngliche Person oder jemand mit Admin-/Manage-Messages-Rechten
    darf einen Eintrag über die Forum-Buttons bearbeiten oder löschen."""
    if entry.get("ersteller_id") == interaction.user.id:
        return True
    if isinstance(interaction.channel, (discord.Thread, discord.TextChannel, discord.ForumChannel)):
        perms = interaction.channel.permissions_for(interaction.user)  # type: ignore[union-attr]
        return bool(perms.administrator or perms.manage_messages)
    return False


class ForumEditModal(ui.Modal, title="Eintrag bearbeiten"):
    name = ui.TextInput(label="Name", max_length=100)
    koordinaten = ui.TextInput(label="Koordinaten (X Y Z oder X Z)", max_length=100)
    beschreibung = ui.TextInput(
        label="Beschreibung (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500,
    )

    def __init__(self, entry: Dict[str, Any]) -> None:
        super().__init__()
        self.entry_id = entry["id"]
        self.category = entry["typ"]
        self.title = f"Bearbeiten: {entry['name']}"[:45]
        self.name.default = entry["name"]
        self.koordinaten.default = _format_coords_input(entry)
        self.beschreibung.default = entry.get("beschreibung") or None

        self.specs_input: Optional[ui.TextInput] = None
        if self.category in _FARM_LABELS:
            self.specs_input = ui.TextInput(
                label="Farm-Specs (optional)",
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=500,
            )
            self.specs_input.default = entry.get("specs") or None
            self.add_item(self.specs_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        parts = self.koordinaten.value.replace(",", " ").split()
        try:
            if len(parts) == 3:
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
            elif len(parts) == 2:
                x, z = float(parts[0]), float(parts[1])
                y = None
            else:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Konnte die Koordinaten nicht lesen. Bitte im Format `X Y Z` oder `X Z` angeben.",
                ephemeral=True,
            )
            return

        specs_value = None
        if self.specs_input and self.specs_input.value:
            specs_value = self.specs_input.value.strip() or None
        beschreibung_value = self.beschreibung.value.strip() if self.beschreibung.value else None

        await db.update_entry(
            self.entry_id,
            name=self.name.value.strip(),
            x=x,
            y=y,
            z=z,
            beschreibung=beschreibung_value,
            specs=specs_value,
        )

        await interaction.response.send_message("✅ Eintrag wurde aktualisiert.", ephemeral=True)

        await log_action(
            interaction.guild,
            discord.Embed(
                title="✏️ Eintrag bearbeitet",
                description=(
                    f"{_category_emoji(self.category)} **{self.name.value.strip()}** ({self.category}) "
                    f"ID `{self.entry_id}`\nBearbeitet von: {interaction.user.mention}"
                ),
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow(),
            ),
        )

        await _sync_forum_post(interaction.guild, self.entry_id)


class ForumEditButton(discord.ui.DynamicItem[discord.ui.Button], template=r"forum_edit:(?P<entry_id>\d+)"):
    """Persistenter 'Bearbeiten'-Button in Farm-Forum-Beiträgen (übersteht Bot-Neustarts)."""

    def __init__(self, entry_id: int) -> None:
        super().__init__(
            discord.ui.Button(
                label="✏️ Bearbeiten",
                style=discord.ButtonStyle.primary,
                custom_id=f"forum_edit:{entry_id}",
            )
        )
        self.entry_id = entry_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: discord.ui.Button, match: "re.Match[str]"
    ) -> "ForumEditButton":
        return cls(int(match["entry_id"]))

    async def callback(self, interaction: discord.Interaction) -> None:
        entry = await db.get_entry(self.entry_id)
        if not entry:
            await interaction.response.send_message("❌ Dieser Eintrag existiert nicht mehr.", ephemeral=True)
            return
        if not await _can_edit_or_delete(interaction, entry):
            await interaction.response.send_message(
                "❌ Nur die Person, die den Eintrag erstellt hat, oder ein Admin kann ihn bearbeiten.",
                ephemeral=True,
            )
            return
        actions_view = EditActionsView(entry)
        await interaction.response.send_message(
            f"✏️ Was möchtest du an **{entry['name']}** (ID {entry['id']}) ändern?",
            view=actions_view,
            ephemeral=True,
        )


class ForumDeleteButton(discord.ui.DynamicItem[discord.ui.Button], template=r"forum_delete:(?P<entry_id>\d+)"):
    """Persistenter 'Löschen'-Button in Farm-Forum-Beiträgen (übersteht Bot-Neustarts)."""

    def __init__(self, entry_id: int) -> None:
        super().__init__(
            discord.ui.Button(
                label="🗑️ Löschen",
                style=discord.ButtonStyle.danger,
                custom_id=f"forum_delete:{entry_id}",
            )
        )
        self.entry_id = entry_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: discord.ui.Button, match: "re.Match[str]"
    ) -> "ForumDeleteButton":
        return cls(int(match["entry_id"]))

    async def callback(self, interaction: discord.Interaction) -> None:
        entry = await db.get_entry(self.entry_id)
        if not entry:
            await interaction.response.send_message("❌ Dieser Eintrag existiert nicht mehr.", ephemeral=True)
            return
        if not await _can_edit_or_delete(interaction, entry):
            await interaction.response.send_message(
                "❌ Nur die Person, die den Eintrag erstellt hat, oder ein Admin kann ihn löschen.",
                ephemeral=True,
            )
            return

        await db.delete_entry(self.entry_id)
        await interaction.response.send_message(
            f"🗑️ **{entry['name']}** wurde gelöscht. Dieser Forum-Beitrag wird nun ebenfalls entfernt.",
            ephemeral=True,
        )

        await log_action(
            interaction.guild,
            discord.Embed(
                title="🗑️ Eintrag gelöscht",
                description=(
                    f"{_category_emoji(entry['typ'])} **{entry['name']}** ({entry['typ']}) "
                    f"ID `{entry['id']}`\nGelöscht über Forum-Beitrag von: {interaction.user.mention}"
                ),
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            ),
        )

        thread = interaction.channel if isinstance(interaction.channel, discord.Thread) else None
        if thread is not None:
            try:
                await thread.delete()
            except discord.HTTPException:
                pass


def _build_forum_embeds(
    name: str,
    category: str,
    coord_str: str,
    beschreibung: Optional[str],
    specs: Optional[str],
    creator: str,
    entry_id: int,
    images: List[Dict[str, Any]],
    tags: Optional[str] = None,
    youtube_link: Optional[str] = None,
    custom_color: Optional[str] = None,
) -> List[discord.Embed]:
    """
    Baut ein übersichtliches Embed-Set für den Forum-Beitrag: ein Haupt-Embed
    mit den Eckdaten, ein separates Details-Embed für Beschreibung/Specs/Tags/
    YouTube-Link (falls vorhanden) und je ein eigenes Embed pro Bild inkl.
    Bildbeschreibung als Footer.
    """
    emoji = _category_emoji(category)
    color = _resolve_color(category, custom_color)

    main = discord.Embed(
        title=f"{emoji} {name}",
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    main.add_field(name="📍 Koordinaten", value=f"`{coord_str}`", inline=True)
    main.add_field(name="🏷️ Kategorie", value=category, inline=True)
    main.add_field(name="🆔 ID", value=f"`{entry_id}`", inline=True)
    main.set_footer(text=f"Eingetragen von {creator}")

    embeds = [main]

    if beschreibung or specs or tags or youtube_link:
        details = discord.Embed(title="📋 Details", color=color)
        if beschreibung:
            details.add_field(name="📝 Beschreibung", value=beschreibung, inline=False)
        if specs:
            details.add_field(name="🔧 Specs", value=specs, inline=False)
        if tags:
            details.add_field(name="🏷️ Tags", value=tags, inline=False)
        if youtube_link:
            details.add_field(name="▶️ Tutorial", value=youtube_link, inline=False)
        embeds.append(details)

    # Jedes Bild bekommt ein eigenes Embed inkl. Bildbeschreibung als Footer -
    # Discord erlaubt max. 10 Embeds pro Nachricht insgesamt.
    remaining_slots = 10 - len(embeds)
    for img in images[:remaining_slots]:
        img_embed = discord.Embed(color=color)
        img_embed.set_image(url=img["url"])
        if img.get("caption"):
            img_embed.set_footer(text=img["caption"])
        embeds.append(img_embed)

    return embeds


# --------------------------------------------------------------------------- #
# Gemeinsam: paginiertes & durchsuchbares Auswahl-Dropdown (Schritt 2)
# --------------------------------------------------------------------------- #

class CategorySelect(ui.Select):
    """Das eigentliche Dropdown einer Seite. Ruft beim Auswählen view.on_pick() auf."""

    def __init__(self, options: List[discord.SelectOption]) -> None:
        super().__init__(placeholder="Auswählen ...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "PagedCategoryView" = self.view  # type: ignore[assignment]
        await view.on_pick(interaction, self.values[0])


class PagePrevButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="◀ Zurück", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "PagedCategoryView" = self.view  # type: ignore[assignment]
        view.page -= 1
        view.rebuild()
        await interaction.response.edit_message(content=view.render_content(), view=view)


class PageNextButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="Weiter ▶", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "PagedCategoryView" = self.view  # type: ignore[assignment]
        view.page += 1
        view.rebuild()
        await interaction.response.edit_message(content=view.render_content(), view=view)


class CategoryFilterModal(ui.Modal, title="Suche"):
    suchbegriff = ui.TextInput(
        label="Suchbegriff",
        placeholder="z.B. ocean, forest, farm ...",
        max_length=100,
    )

    def __init__(self, paged_view: "PagedCategoryView") -> None:
        super().__init__()
        self.paged_view = paged_view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.paged_view.apply_filter(self.suchbegriff.value.strip())
        await interaction.response.edit_message(
            content=self.paged_view.render_content(), view=self.paged_view
        )


class FilterButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="🔍 Suche", style=discord.ButtonStyle.primary, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "PagedCategoryView" = self.view  # type: ignore[assignment]
        await interaction.response.send_modal(CategoryFilterModal(view))


class ResetFilterButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="✖ Filter zurücksetzen", style=discord.ButtonStyle.secondary, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "PagedCategoryView" = self.view  # type: ignore[assignment]
        view.apply_filter("")
        await interaction.response.edit_message(content=view.render_content(), view=view)


class PagedCategoryView(ui.View):
    """
    Zeigt bis zu 25 Optionen pro Seite in einem Dropdown. Hat die (ggf. gefilterte)
    Liste mehr Einträge, werden zusätzlich Pfeil-Buttons zum Blättern angezeigt.
    Über den Such-Button kann die Liste per Modal nach einem Suchbegriff gefiltert
    werden, damit man nicht lange scrollen muss.
    `items` ist eine Liste von (Anzeigename, Wert, Emoji)-Tupeln.
    """

    PAGE_SIZE = 25

    def __init__(
        self,
        items: List[Tuple[str, str, str]],
        prompt: str,
        all_filter: Optional[List[str]] = None,
        all_label: str = "Alle",
    ) -> None:
        super().__init__(timeout=180)
        self.all_items = items
        self.items = items
        self.prompt = prompt
        self.page = 0
        self.filter_term = ""
        # all_filter: bei Auswahl von "Alle Strukturen"/"Alle Biome"/"Alle Farmen"
        # wird damit gefiltert (Liste der konkreten Typen), statt gar nicht zu filtern.
        self.all_filter = all_filter
        self.all_label = all_label
        self.rebuild()

    def apply_filter(self, term: str) -> None:
        self.filter_term = term.strip()
        if self.filter_term:
            needle = self.filter_term.lower()
            self.items = [i for i in self.all_items if needle in i[0].lower()]
        else:
            self.items = self.all_items
        self.page = 0
        self.rebuild()

    @property
    def max_page(self) -> int:
        return max(0, (len(self.items) - 1) // self.PAGE_SIZE) if self.items else 0

    def render_content(self) -> str:
        content = self.prompt
        if self.filter_term:
            content += f"\n🔍 Filter: `{self.filter_term}` – {len(self.items)} Treffer"
        if self.max_page > 0:
            content += f" (Seite {self.page + 1}/{self.max_page + 1})"
        if self.filter_term and not self.items:
            content += "\n❌ Nichts gefunden, versuche einen anderen Suchbegriff."
        return content

    def rebuild(self) -> None:
        self.clear_items()

        if self.items:
            start = self.page * self.PAGE_SIZE
            page_items = self.items[start:start + self.PAGE_SIZE]
            options = [
                discord.SelectOption(label=label, value=value, emoji=emoji)
                for label, value, emoji in page_items
            ]
            self.add_item(CategorySelect(options))

        if self.max_page > 0:
            prev_btn = PagePrevButton()
            next_btn = PageNextButton()
            prev_btn.disabled = self.page <= 0
            next_btn.disabled = self.page >= self.max_page
            self.add_item(prev_btn)
            self.add_item(next_btn)

        self.add_item(FilterButton())
        if self.filter_term:
            self.add_item(ResetFilterButton())

    async def on_pick(self, interaction: discord.Interaction, value: str) -> None:
        raise NotImplementedError


class EntryPagedCategoryView(PagedCategoryView):
    async def on_pick(self, interaction: discord.Interaction, value: str) -> None:
        await interaction.response.send_modal(EntryModal(category=value))


class SearchPagedCategoryView(PagedCategoryView):
    async def on_pick(self, interaction: discord.Interaction, value: str) -> None:
        if value == "__all__":
            await interaction.response.send_modal(
                SearchModal(category_filter=self.all_filter, display_label=self.all_label)
            )
        else:
            await interaction.response.send_modal(
                SearchModal(category_filter=value, display_label=value)
            )


class DeletePagedCategoryView(PagedCategoryView):
    async def on_pick(self, interaction: discord.Interaction, value: str) -> None:
        if value == "__all__":
            await interaction.response.send_modal(
                DeleteSearchModal(category_filter=self.all_filter, display_label=self.all_label)
            )
        else:
            await interaction.response.send_modal(
                DeleteSearchModal(category_filter=value, display_label=value)
            )


# --------------------------------------------------------------------------- #
# Gemeinsam: Struktur/Biom/Farm-Auswahl (Schritt 1)
# --------------------------------------------------------------------------- #

class TypeSelect(ui.Select):
    """Erster Dropdown-Schritt: Struktur, Biom, Farm oder Base? Unterklassen legen
    fest, was danach passiert."""

    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="Struktur", value="struktur", emoji="🏛️"),
            discord.SelectOption(label="Biom", value="biom", emoji="🌳"),
            discord.SelectOption(label="Farm", value="farm", emoji="🚜"),
            discord.SelectOption(label="Base", value="base", emoji="🏠"),
        ]
        super().__init__(
            placeholder="Struktur, Biom, Farm oder Base?", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Bilder nachträglich beschreiben (nach dem Hochladen)
# --------------------------------------------------------------------------- #

class ImageCaptionModal(ui.Modal, title="Bild beschreiben"):
    beschreibung = ui.TextInput(
        label="Beschreibung für dieses Bild",
        style=discord.TextStyle.paragraph,
        placeholder="z.B. Blick auf den Eingang, Redstone-Verkabelung, ...",
        max_length=200,
    )

    def __init__(self, gallery: "ImageCaptionView", image_id: int) -> None:
        super().__init__()
        self.gallery = gallery
        self.image_id = image_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        caption = self.beschreibung.value.strip()
        await db.set_image_caption(self.image_id, caption)
        self.gallery.captions[self.image_id] = caption
        await interaction.response.edit_message(
            content=self.gallery.render_content(), embed=self.gallery.build_embed(), view=self.gallery
        )
        # Falls die Farm bereits einen Forum-Beitrag hat, diesen mit der neuen
        # Bildbeschreibung aktualisieren.
        await _sync_forum_post(interaction.guild, self.gallery.entry_id)


class ImageCaptionPrevButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="◀", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ImageCaptionView" = self.view  # type: ignore[assignment]
        view.index -= 1
        view.rebuild_buttons()
        await interaction.response.edit_message(
            content=view.render_content(), embed=view.build_embed(), view=view
        )


class ImageCaptionNextButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="▶", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ImageCaptionView" = self.view  # type: ignore[assignment]
        view.index += 1
        view.rebuild_buttons()
        await interaction.response.edit_message(
            content=view.render_content(), embed=view.build_embed(), view=view
        )


class ImageCaptionSetButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="✏️ Beschreibung setzen", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ImageCaptionView" = self.view  # type: ignore[assignment]
        image_id = view.images[view.index]["id"]
        await interaction.response.send_modal(ImageCaptionModal(view, image_id))


class ImageCaptionView(ui.View):
    """Kleine Galerie zum nachträglichen Beschriften der gerade hochgeladenen Bilder."""

    def __init__(self, entry_id: int, images: List[Dict[str, Any]]) -> None:
        super().__init__(timeout=300)
        self.entry_id = entry_id
        self.images = images
        self.index = 0
        self.captions: Dict[int, Optional[str]] = {img["id"]: img.get("caption") for img in images}
        self.rebuild_buttons()

    def rebuild_buttons(self) -> None:
        self.clear_items()
        prev_btn = ImageCaptionPrevButton()
        next_btn = ImageCaptionNextButton()
        prev_btn.disabled = self.index <= 0
        next_btn.disabled = self.index >= len(self.images) - 1
        self.add_item(prev_btn)
        self.add_item(next_btn)
        self.add_item(ImageCaptionSetButton())

    def render_content(self) -> str:
        return f"Bild {self.index + 1} von {len(self.images)} – klicke auf ✏️, um eine Beschreibung zu setzen."

    def build_embed(self) -> discord.Embed:
        img = self.images[self.index]
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_image(url=img["url"])
        caption = self.captions.get(img["id"])
        embed.description = caption if caption else "_Noch keine Beschreibung._"
        return embed


class ImageSavedOpenGalleryButton(ui.Button):
    def __init__(self, entry_id: int, images: List[Dict[str, Any]]) -> None:
        super().__init__(label="📝 Bilder beschreiben", style=discord.ButtonStyle.secondary)
        self.entry_id = entry_id
        self.images = images

    async def callback(self, interaction: discord.Interaction) -> None:
        gallery = ImageCaptionView(self.entry_id, self.images)
        await interaction.response.edit_message(
            content=gallery.render_content(), embed=gallery.build_embed(), view=gallery
        )


class ImageSavedView(ui.View):
    """Wird nach dem Speichern der Bilder gezeigt, mit Button zum Beschriften."""

    def __init__(self, entry_id: int, images: List[Dict[str, Any]]) -> None:
        super().__init__(timeout=300)
        if images:
            self.add_item(ImageSavedOpenGalleryButton(entry_id, images))


class FinishUploadView(ui.View):
    """Button, mit dem der Bild-Upload beendet wird (statt 'fertig' zu schreiben)."""

    def __init__(self, user_id: int) -> None:
        super().__init__(timeout=185)
        self.user_id = user_id
        self.done_event = asyncio.Event()

    @ui.button(label="✅ Fertig", style=discord.ButtonStyle.success)
    async def finish_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Das ist nicht dein Bild-Upload.", ephemeral=True)
            return
        self.done_event.set()
        button.disabled = True
        button.label = "✅ Abgeschlossen"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self) -> None:
        self.done_event.set()


# --------------------------------------------------------------------------- #
# Tags & YouTube-Link (optional, nach dem Eintragen)
# --------------------------------------------------------------------------- #

# Vorgeschlagene Tags zur Auswahl - eigene Tags können zusätzlich frei getippt werden.
PRESET_TAGS: List[str] = ["Overworld", "Nether", "End", "Automatisch", "Semi-Automatisch", "Passiv-Automatisch", "AFK"]


class YoutubeLinkModal(ui.Modal, title="YouTube-Tutorial verlinken"):
    youtube_link = ui.TextInput(
        label="YouTube-Link (optional)",
        placeholder="z.B. https://youtu.be/... oder leer lassen",
        required=False,
        max_length=200,
    )

    def __init__(self, tags_view: "TagsView") -> None:
        super().__init__()
        self.tags_view = tags_view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        link = self.youtube_link.value.strip() if self.youtube_link.value else None
        if link and "youtu" not in link.lower():
            await interaction.response.send_message(
                "❌ Das sieht nicht nach einem YouTube-Link aus. Bitte einen gültigen Link "
                "angeben oder das Feld leer lassen.",
                ephemeral=True,
            )
            return

        tags_str = self.tags_view.tags_string()
        await db.set_entry_tags(self.tags_view.entry_id, tags_str)
        await db.set_entry_youtube(self.tags_view.entry_id, link)

        summary = []
        if tags_str:
            summary.append(f"🏷️ Tags: {tags_str}")
        if link:
            summary.append(f"▶️ Tutorial: {link}")
        text = "✅ Gespeichert!" + ("\n" + "\n".join(summary) if summary else " (keine Tags/Video hinterlegt)")

        await interaction.response.edit_message(content=text, view=None)

        # Falls dazu bereits ein Farm-Forum-Beitrag existiert, diesen aktualisieren.
        await _sync_forum_post(interaction.guild, self.tags_view.entry_id)

        # Anschließend optional eine individuelle Embed-Farbe für diesen Eintrag anbieten.
        color_view = ColorView(self.tags_view.entry_id)
        await interaction.followup.send(
            "🎨 Möchtest du für diesen Eintrag eine eigene Embed-Farbe festlegen? (optional, "
            "überschreibt die Standardfarbe der Kategorie)",
            view=color_view,
            ephemeral=True,
        )


# Vorgeschlagene Embed-Farben (Name -> Hex-Wert ohne '#'); "Standard" löscht eine
# zuvor gesetzte eigene Farbe wieder.
PRESET_COLORS: Dict[str, Optional[str]] = {
    "Standard (nach Kategorie)": None,
    "Rot": "E74C3C",
    "Orange": "E67E22",
    "Gelb": "F1C40F",
    "Grün": "2ECC71",
    "Blau": "3498DB",
    "Lila": "9B59B6",
    "Pink": "E91E63",
    "Türkis": "1ABC9C",
    "Grau": "95A5A6",
}


class ColorSelect(ui.Select):
    def __init__(self) -> None:
        options = [discord.SelectOption(label=name) for name in PRESET_COLORS]
        super().__init__(
            placeholder="Embed-Farbe auswählen (optional)",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ColorView" = self.view  # type: ignore[assignment]
        color_hex = PRESET_COLORS[self.values[0]]
        await view.save_color(interaction, color_hex)


class CustomColorModal(ui.Modal, title="Eigene Farbe (Hex)"):
    hex_code = ui.TextInput(
        label="Hex-Farbcode",
        placeholder="z.B. #FF5733 oder FF5733",
        max_length=7,
    )

    def __init__(self, color_view: "ColorView") -> None:
        super().__init__()
        self.color_view = color_view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = self.hex_code.value.strip().lstrip("#")
        if len(raw) != 6 or not all(c in "0123456789abcdefABCDEF" for c in raw):
            await interaction.response.send_message(
                "❌ Ungültiger Hex-Code. Bitte im Format `#RRGGBB` angeben (z.B. `#FF5733`).",
                ephemeral=True,
            )
            return
        await self.color_view.save_color(interaction, raw.upper())


class CustomColorButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="🎨 Eigene Farbe (Hex)", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ColorView" = self.view  # type: ignore[assignment]
        await interaction.response.send_modal(CustomColorModal(view))


class SkipColorButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="⏭️ Überspringen", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ColorView" = self.view  # type: ignore[assignment]
        await view.save_color(interaction, None)


class ColorView(ui.View):
    """Optionale Ansicht zum Festlegen einer individuellen Embed-Farbe pro Eintrag."""

    def __init__(self, entry_id: int) -> None:
        super().__init__(timeout=180)
        self.entry_id = entry_id
        self.add_item(ColorSelect())
        self.add_item(CustomColorButton())
        self.add_item(SkipColorButton())

    async def save_color(self, interaction: discord.Interaction, color_hex: Optional[str]) -> None:
        await db.set_entry_color(self.entry_id, color_hex)
        text = (
            f"✅ Individuelle Embed-Farbe gespeichert: `#{color_hex}`"
            if color_hex
            else "✅ Es wird die Standardfarbe der Kategorie verwendet."
        )
        await interaction.response.edit_message(content=text, view=None)
        await _sync_forum_post(interaction.guild, self.entry_id)


class TagPresetSelect(ui.Select):
    def __init__(self, selected: List[str]) -> None:
        options = [
            discord.SelectOption(label=tag, value=tag, default=(tag in selected))
            for tag in PRESET_TAGS
        ]
        super().__init__(
            placeholder="Vorgeschlagene Tags auswählen (Mehrfachauswahl möglich)",
            min_values=0,
            max_values=len(options),
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "TagsView" = self.view  # type: ignore[assignment]
        view.preset_tags = list(self.values)
        view.rebuild_buttons()
        await interaction.response.edit_message(content=view.render_content(), view=view)


class CustomTagModal(ui.Modal, title="Eigenen Tag hinzufügen"):
    tag = ui.TextInput(label="Tag", placeholder="z.B. Redstone, Survival, 1.21 ...", max_length=30)

    def __init__(self, tags_view: "TagsView") -> None:
        super().__init__()
        self.tags_view = tags_view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        new_tag = self.tag.value.strip()
        if new_tag and new_tag not in self.tags_view.custom_tags:
            self.tags_view.custom_tags.append(new_tag)
        self.tags_view.rebuild_buttons()
        await interaction.response.edit_message(
            content=self.tags_view.render_content(), view=self.tags_view
        )


class AddCustomTagButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="➕ Eigenen Tag hinzufügen", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "TagsView" = self.view  # type: ignore[assignment]
        await interaction.response.send_modal(CustomTagModal(view))


class SaveTagsButton(ui.Button):
    def __init__(self, include_youtube: bool) -> None:
        label = "💾 Weiter (YouTube-Link)" if include_youtube else "💾 Speichern"
        super().__init__(label=label, style=discord.ButtonStyle.success, row=1)
        self.include_youtube = include_youtube

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "TagsView" = self.view  # type: ignore[assignment]
        if self.include_youtube:
            await interaction.response.send_modal(YoutubeLinkModal(view))
            return

        # Struktur/Biom: kein YouTube-Link - Tags direkt speichern und danach
        # nur noch die Farbauswahl anbieten.
        tags_str = view.tags_string()
        await db.set_entry_tags(view.entry_id, tags_str)
        text = f"✅ Tags gespeichert: {tags_str}" if tags_str else "✅ Gespeichert (keine Tags)."
        await interaction.response.edit_message(content=text, view=None)
        await _sync_forum_post(interaction.guild, view.entry_id)

        color_view = ColorView(view.entry_id)
        await interaction.followup.send(
            "🎨 Möchtest du für diesen Eintrag eine eigene Embed-Farbe festlegen? (optional, "
            "überschreibt die Standardfarbe der Kategorie)",
            view=color_view,
            ephemeral=True,
        )


class TagsView(ui.View):
    """
    Optionale Ansicht nach dem Eintragen: vorgeschlagene Tags (Overworld/Nether/End)
    per Dropdown auswählen, eigene Tags frei hinzufügen. Bei Farmen kann danach noch
    ein YouTube-Tutorial-Link hinterlegt werden; bei Struktur/Biom entfällt dieser
    Schritt und es geht direkt weiter zur Farbauswahl.
    """

    def __init__(self, entry_id: int, include_youtube: bool = True) -> None:
        super().__init__(timeout=300)
        self.entry_id = entry_id
        self.include_youtube = include_youtube
        self.preset_tags: List[str] = []
        self.custom_tags: List[str] = []
        self.rebuild_buttons()

    def all_tags(self) -> List[str]:
        return self.preset_tags + [t for t in self.custom_tags if t not in self.preset_tags]

    def tags_string(self) -> Optional[str]:
        tags = self.all_tags()
        return ", ".join(tags) if tags else None

    def rebuild_buttons(self) -> None:
        self.clear_items()
        self.add_item(TagPresetSelect(self.preset_tags))
        self.add_item(AddCustomTagButton())
        self.add_item(SaveTagsButton(self.include_youtube))

    def render_content(self) -> str:
        tags_display = ", ".join(self.all_tags()) if self.all_tags() else "_noch keine_"
        next_step = "einen YouTube-Tutorial-Link" if self.include_youtube else "die Embed-Farbe"
        return (
            f"🏷️ Wähle passende Tags aus oder füge eigene hinzu, danach geht es weiter zu {next_step} "
            f"(Button \"💾 {'Weiter' if self.include_youtube else 'Speichern'}\").\n"
            f"**Aktuelle Tags:** {tags_display}"
        )


# --------------------------------------------------------------------------- #
# Duplikat-Warnung (Struktur/Biom im Umkreis von 100 Blöcken)
# --------------------------------------------------------------------------- #

class DuplicateConfirmView(ui.View):
    """Nachfrage, falls im Umkreis von 100 Blöcken bereits derselbe Typ existiert."""

    def __init__(self, modal: "EntryModal") -> None:
        super().__init__(timeout=120)
        self.modal = modal

    async def build_nearby_embeds(self, nearby: Dict[str, Any]) -> List[discord.Embed]:
        emoji = _category_emoji(nearby["typ"])
        color = _resolve_color(nearby["typ"], nearby.get("color"))
        embed = discord.Embed(
            title=f"{emoji} In der Nähe: {nearby['name']}",
            color=color,
        )
        embed.add_field(name="Kategorie", value=nearby["typ"], inline=True)
        embed.add_field(name="Koordinaten", value=f"`{_format_coords(nearby)}`", inline=True)
        embed.add_field(name="Entfernung", value=f"~{nearby['distanz']:.0f} Blöcke", inline=True)
        if nearby.get("beschreibung"):
            embed.add_field(name="Beschreibung", value=nearby["beschreibung"], inline=False)
        embed.set_footer(
            text=f"Eingetragen von {nearby.get('ersteller_name', 'Unbekannt')} · ID {nearby['id']}"
        )

        embeds = [embed]
        images = await db.get_images_full(nearby["id"])
        for img in images[:MAX_IMAGE_EMBEDS]:
            img_embed = discord.Embed(color=color)
            img_embed.set_image(url=img["url"])
            if img.get("caption"):
                img_embed.set_footer(text=img["caption"])
            embeds.append(img_embed)
        return embeds

    @ui.button(label="✅ Trotzdem eintragen", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(view=self)
        await self.modal._finalize_entry(interaction)

    @ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await interaction.response.edit_message(
            content="❌ Eintragen abgebrochen.", embeds=[], view=None
        )


# --------------------------------------------------------------------------- #
# Eintragen
# --------------------------------------------------------------------------- #

class EntryModal(ui.Modal, title="Neuen Eintrag erstellen"):
    name = ui.TextInput(
        label="Name der Struktur/des Bioms/der Farm",
        placeholder="z.B. Woodland Mansion, Wüste Nr. 3, Iron Farm Spawn ...",
        max_length=100,
    )
    koordinaten = ui.TextInput(
        label="Koordinaten (X Y Z oder X Z)",
        placeholder="z.B. 120 65 -430",
        max_length=100,
    )
    beschreibung = ui.TextInput(
        label="Beschreibung (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500,
    )

    def __init__(self, category: str) -> None:
        super().__init__()
        self.category = category
        self.title = f"Eintragen: {category}"[:45]

        # Bei Farmen gibt es zusätzlich ein Feld für die Specs (Rate, AFK-Spot, ...).
        self.specs_input: Optional[ui.TextInput] = None
        if category in _FARM_LABELS:
            self.specs_input = ui.TextInput(
                label="Farm-Specs (optional)",
                style=discord.TextStyle.paragraph,
                placeholder="z.B. Rate: ~3000 Eisen/h · AFK bei Y=200 · Redstone: Slime-Klock",
                required=False,
                max_length=500,
            )
            self.add_item(self.specs_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        parts = self.koordinaten.value.replace(",", " ").split()
        try:
            if len(parts) == 3:
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
            elif len(parts) == 2:
                x, z = float(parts[0]), float(parts[1])
                y = None
            else:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Konnte die Koordinaten nicht lesen. Bitte im Format `X Y Z` oder `X Z` angeben.",
                ephemeral=True,
            )
            return

        self._x, self._y, self._z = x, y, z

        # Bei Struktur/Biom (nicht bei Farmen) prüfen, ob im Umkreis von 100
        # Blöcken bereits ein Eintrag desselben Typs existiert - dann erst
        # nachfragen, statt direkt zu speichern.
        if self.category in _STRUCTURE_LABELS or self.category in _BIOME_LABELS:
            nearby = await self._find_nearby_same_type(x, z)
            if nearby:
                view = DuplicateConfirmView(self)
                embeds = await view.build_nearby_embeds(nearby)
                await interaction.response.send_message(
                    content=(
                        f"⚠️ Im Umkreis von 100 Blöcken existiert bereits ein Eintrag vom Typ "
                        f"**{self.category}** (~{nearby['distanz']:.0f} Blöcke entfernt). "
                        "Möchtest du **{}** trotzdem eintragen?".format(self.name.value.strip())
                    ),
                    embeds=embeds,
                    view=view,
                    ephemeral=True,
                )
                return

        await interaction.response.defer(ephemeral=True)
        await self._finalize_entry(interaction)

    async def _find_nearby_same_type(self, x: float, z: float) -> Optional[Dict[str, Any]]:
        """Liefert den nächstgelegenen bestehenden Eintrag desselben Typs im
        Umkreis von 100 Blöcken (nur X/Z), falls vorhanden."""
        existing = await db.search_entries(term="", typ=self.category)
        nearest: Optional[Dict[str, Any]] = None
        nearest_dist: Optional[float] = None
        for e in existing:
            dist = math.dist((x, z), (e["x"], e["z"]))
            if dist <= 100 and (nearest_dist is None or dist < nearest_dist):
                nearest = dict(e)
                nearest_dist = dist
        if nearest is not None:
            nearest["distanz"] = nearest_dist
        return nearest

    async def _finalize_entry(self, interaction: discord.Interaction) -> None:
        """Legt den Eintrag tatsächlich an (nach evtl. Duplikat-Bestätigung)."""
        x, y, z = self._x, self._y, self._z

        specs_value = None
        if self.specs_input and self.specs_input.value:
            specs_value = self.specs_input.value.strip() or None

        entry_id = await db.add_entry(
            name=self.name.value.strip(),
            typ=self.category,
            x=x,
            y=y,
            z=z,
            beschreibung=self.beschreibung.value.strip() if self.beschreibung.value else None,
            ersteller_id=interaction.user.id,
            ersteller_name=str(interaction.user),
            specs=specs_value,
        )

        coord_str = f"X: {x} | Y: {y} | Z: {z}" if y is not None else f"X: {x} | Z: {z}"
        emoji = _category_emoji(self.category)

        # Für den Forum-Beitrag (wird erst NACH dem Bild-Upload erstellt) merken.
        self._coord_str = coord_str
        self._specs_value = specs_value
        self._beschreibung_value = self.beschreibung.value.strip() if self.beschreibung.value else None

        embed = discord.Embed(
            title=f"{emoji} {self.name.value.strip()}",
            color=_category_color(self.category),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Kategorie", value=self.category, inline=True)
        embed.add_field(name="Koordinaten", value=f"`{coord_str}`", inline=True)
        embed.add_field(name="ID", value=f"`{entry_id}`", inline=True)
        if self.beschreibung.value:
            embed.add_field(name="Beschreibung", value=self.beschreibung.value, inline=False)
        if specs_value:
            embed.add_field(name="🔧 Specs", value=specs_value, inline=False)
        embed.set_footer(
            text=f"Eingetragen von {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.followup.send(content="✅ Eintrag gespeichert!", embed=embed, ephemeral=True)

        # Tags gibt es bei jeder Kategorie (z.B. Overworld/Nether/End). Der
        # YouTube-Link-Schritt danach ist nur bei Farmen sinnvoll (Tutorials) -
        # bei Struktur/Biom geht es nach den Tags direkt zur Farbauswahl.
        include_youtube = self.category in _FARM_LABELS
        tags_view = TagsView(entry_id, include_youtube=include_youtube)
        await interaction.followup.send(tags_view.render_content(), view=tags_view, ephemeral=True)

        finish_view = FinishUploadView(interaction.user.id)
        prompt_message = await interaction.followup.send(
            f"📸 Du kannst jetzt bis zu 3 Minuten lang Bild(er) zu **{self.name.value.strip()}** "
            f"in diesen Channel senden. Deine Nachrichten mit den Bildern werden danach automatisch "
            f"wieder gelöscht. Klicke auf **✅ Fertig**, wenn du keine weiteren Bilder hochladen möchtest.\n"
            f"-# ℹ️ Hinweis: Der Eintrag wurde bereits gespeichert - der Fertig-Button schließt nur "
            f"den Bild-Upload ab, er erstellt den Eintrag nicht erneut.",
            view=finish_view,
            ephemeral=True,
        )

        await log_action(
            interaction.guild,
            discord.Embed(
                title="📍 Neuer Eintrag",
                description=(
                    f"{emoji} **{self.name.value.strip()}** ({self.category})\n"
                    f"Koordinaten: `{coord_str}` · ID: `{entry_id}`\nVon: {interaction.user.mention}"
                ),
                color=_category_color(self.category),
                timestamp=discord.utils.utcnow(),
            ),
        )

        # Der Forum-Beitrag für Farmen wird erst in _collect_images erstellt,
        # NACHDEM die Bilder archiviert wurden - so landen die Bilder auch
        # tatsächlich im Beitrag.
        await self._collect_images(interaction, entry_id, finish_view, prompt_message)

    async def _collect_images(
        self,
        interaction: discord.Interaction,
        entry_id: int,
        finish_view: "FinishUploadView",
        prompt_message: discord.Message,
    ) -> None:
        bot = interaction.client
        collected_messages: List[discord.Message] = []
        collected_attachments: List[discord.Attachment] = []

        def check(m: discord.Message) -> bool:
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        loop = asyncio.get_event_loop()
        end_time = loop.time() + 180

        while True:
            remaining = end_time - loop.time()
            if remaining <= 0 or finish_view.done_event.is_set():
                break

            # Wettlauf zwischen "neues Bild kommt an" und "Fertig-Button geklickt" -
            # je nachdem was zuerst passiert, wird entsprechend reagiert.
            message_task = asyncio.ensure_future(bot.wait_for("message", check=check))
            done_task = asyncio.ensure_future(finish_view.done_event.wait())

            done, pending = await asyncio.wait(
                {message_task, done_task}, timeout=remaining, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()

            if not done:
                break  # Timeout erreicht

            if done_task in done:
                break  # "✅ Fertig" wurde geklickt

            try:
                msg = message_task.result()
            except Exception:
                break

            image_attachments = [
                att for att in msg.attachments
                if att.content_type and att.content_type.startswith("image/")
            ]
            if image_attachments:
                collected_messages.append(msg)
                collected_attachments.extend(image_attachments)
            # Nachrichten ohne Bild werden ignoriert (nicht gelöscht), damit der
            # Bot keinen unbeteiligten Chat im Channel löscht.

        finish_view.stop()
        try:
            await prompt_message.edit(content="⏳ Bild-Upload beendet, verarbeite Bilder ...", view=None)
        except discord.HTTPException:
            pass

        # Bilder dauerhaft in den Archiv-Channel kopieren, BEVOR die Original-
        # Nachrichten gelöscht werden - sonst würde Discord die Bild-Dateien
        # mitlöschen und die gespeicherten Links wären ungültig. Alle Bilder
        # werden dabei in möglichst wenigen Nachrichten (max. 10 Anhänge pro
        # Discord-Nachricht) zusammen gruppiert, statt einzeln verschickt.
        saved_urls: List[str] = []
        if collected_attachments and interaction.guild is not None:
            try:
                archive_channel = await _get_image_channel(interaction.guild)
                files = [await att.to_file() for att in collected_attachments]
                for i in range(0, len(files), 10):
                    chunk = files[i:i + 10]
                    archive_msg = await archive_channel.send(
                        content=(
                            f"Bilder zu Eintrag #{entry_id} (eingetragen von {interaction.user})"
                            if i == 0
                            else None
                        ),
                        files=chunk,
                    )
                    saved_urls.extend(att.url for att in archive_msg.attachments)
            except discord.HTTPException:
                pass

        # Erst jetzt - nachdem die Bilder sicher archiviert sind - die
        # ursprünglichen Nachrichten gesammelt löschen.
        for m in collected_messages:
            try:
                await m.delete()
            except discord.HTTPException:
                pass

        images_full: List[Dict[str, Any]] = []
        if saved_urls:
            await db.add_images(entry_id, saved_urls)
            images_full = await db.get_images_full(entry_id)
            await interaction.followup.send(
                f"🖼️ {len(saved_urls)} Bild(er) gespeichert.",
                view=ImageSavedView(entry_id, images_full),
                ephemeral=True,
            )
            await log_action(
                interaction.guild,
                discord.Embed(
                    title="🖼️ Bilder hinzugefügt",
                    description=(
                        f"{len(saved_urls)} Bild(er) zu Eintrag #{entry_id} von "
                        f"{interaction.user.mention} hinzugefügt."
                    ),
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow(),
                ),
            )
        else:
            await interaction.followup.send(
                "ℹ️ Kein Bild hochgeladen, Eintrag wurde ohne Bild gespeichert.", ephemeral=True
            )

        # Forum-Beitrag erst JETZT erstellen (falls für diese Kategorie ein
        # Forum-Channel verknüpft ist) - so sind eventuell hochgeladene Bilder
        # bereits archiviert und können mit reinschrieben werden.
        # Frisch aus der DB laden, falls Tags/YouTube-Link/Farbe schon gesetzt
        # wurden, während noch Bilder hochgeladen wurden.
        current_entry = await db.get_entry(entry_id)
        forum_embeds = _build_forum_embeds(
            name=self.name.value.strip(),
            category=self.category,
            coord_str=self._coord_str,
            beschreibung=self._beschreibung_value,
            specs=self._specs_value,
            tags=current_entry.get("tags") if current_entry else None,
            youtube_link=current_entry.get("youtube_link") if current_entry else None,
            custom_color=current_entry.get("color") if current_entry else None,
            creator=str(interaction.user),
            entry_id=entry_id,
            images=images_full,
        )
        await _create_forum_post(
            interaction.guild,
            entry_id,
            self.name.value.strip(),
            self.category,
            forum_embeds,
            tags=current_entry.get("tags") if current_entry else None,
        )


class EntryTypeSelect(TypeSelect):
    async def callback(self, interaction: discord.Interaction) -> None:
        source, prompt, _ = _GROUPS[self.values[0]]
        items = [(label, label, emoji) for label, emoji in source]
        view = EntryPagedCategoryView(items, prompt)
        await interaction.response.edit_message(content=view.render_content(), view=view)


class EntryTypeView(ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=120)
        self.add_item(EntryTypeSelect())


class EntryView(ui.View):
    """Persistente View mit dem 'Eintragen'-Button (funktioniert auch nach Bot-Neustart)."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @ui.button(label="📍 Eintragen", style=discord.ButtonStyle.green, custom_id="entry_button")
    async def entry_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await interaction.response.send_message(
            "Ist es eine Struktur, ein Biom, eine Farm oder eine Base?", view=EntryTypeView(), ephemeral=True
        )


# --------------------------------------------------------------------------- #
# Suchen
# --------------------------------------------------------------------------- #

class SearchModal(ui.Modal, title="Eintrag suchen"):
    suchbegriff = ui.TextInput(
        label="Name (optional, leer = alle in Kategorie)",
        placeholder="z.B. Wüste, Dorf Nr. 2, Iron Farm ...",
        required=False,
        max_length=100,
    )
    eigene_koordinaten = ui.TextInput(
        label="Deine aktuelle Position (optional)",
        placeholder="z.B. 100 -200 (für die Entfernung zur nächsten Fundstelle)",
        required=False,
        max_length=100,
    )

    def __init__(self, category_filter: Optional[Union[str, List[str]]], display_label: str) -> None:
        super().__init__()
        self.category_filter = category_filter
        self.display_label = display_label
        self.title = f"Suchen: {display_label}"[:45]

    async def on_submit(self, interaction: discord.Interaction) -> None:
        term = self.suchbegriff.value.strip() if self.suchbegriff.value else ""
        results = await db.search_entries(term=term, typ=self.category_filter)

        if not results:
            details = []
            if self.category_filter:
                details.append(f"Kategorie **{self.display_label}**")
            if term:
                details.append(f"Name **{term}**")
            suffix = f" für {' und '.join(details)}" if details else ""
            await interaction.response.send_message(f"❌ Keine Einträge gefunden{suffix}.", ephemeral=True)
            return

        origin: Optional[Tuple[float, float]] = None
        if self.eigene_koordinaten.value:
            parts = self.eigene_koordinaten.value.replace(",", " ").split()
            try:
                if len(parts) >= 2:
                    origin = (float(parts[0]), float(parts[1]))
            except ValueError:
                origin = None

        if origin:
            for r in results:
                r["distanz"] = math.dist(origin, (r["x"], r["z"]))
            results.sort(key=lambda r: r["distanz"])

        guild_id = interaction.guild.id if interaction.guild else None
        view = SearchResultsView(results, origin, guild_id=guild_id)
        embeds = await view.build_embeds()
        await interaction.response.send_message(embeds=embeds, view=view, ephemeral=True)


class DistanceModal(ui.Modal, title="Entfernung berechnen"):
    eigene_koordinaten = ui.TextInput(
        label="Deine aktuelle Position (X Z)",
        placeholder="z.B. 100 -200",
        max_length=100,
    )

    def __init__(self, results_view: "SearchResultsView") -> None:
        super().__init__()
        self.results_view = results_view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        parts = self.eigene_koordinaten.value.replace(",", " ").split()
        try:
            origin = (float(parts[0]), float(parts[1]))
        except (ValueError, IndexError):
            await interaction.response.send_message(
                "❌ Konnte die Koordinaten nicht lesen. Bitte im Format `X Z` angeben.", ephemeral=True
            )
            return

        view = self.results_view
        view.origin = origin
        for r in view.results:
            r["distanz"] = math.dist(origin, (r["x"], r["z"]))
        view.results.sort(key=lambda r: r["distanz"])
        view.index = 0
        view.rebuild_buttons()
        embeds = await view.build_embeds()
        await interaction.response.edit_message(embeds=embeds, view=view)


class SearchPrevButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="◀ Zurück", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "SearchResultsView" = self.view  # type: ignore[assignment]
        view.index -= 1
        view.show_images = False
        view.show_specs = False
        view.rebuild_buttons()
        embeds = await view.build_embeds()
        await interaction.response.edit_message(embeds=embeds, view=view)


class SearchNextButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="Weiter ▶", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "SearchResultsView" = self.view  # type: ignore[assignment]
        view.index += 1
        view.show_images = False
        view.show_specs = False
        view.rebuild_buttons()
        embeds = await view.build_embeds()
        await interaction.response.edit_message(embeds=embeds, view=view)


class SearchDistanceButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="📏 Entfernung berechnen", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "SearchResultsView" = self.view  # type: ignore[assignment]
        await interaction.response.send_modal(DistanceModal(view))


class SearchImagesToggleButton(ui.Button):
    def __init__(self, shown: bool) -> None:
        label = "🙈 Bilder verbergen" if shown else "🖼️ Bilder anzeigen"
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "SearchResultsView" = self.view  # type: ignore[assignment]
        view.show_images = not view.show_images
        view.rebuild_buttons()
        embeds = await view.build_embeds()
        await interaction.response.edit_message(embeds=embeds, view=view)


class SearchSpecsToggleButton(ui.Button):
    def __init__(self, shown: bool) -> None:
        label = "🙈 Specs verbergen" if shown else "🔧 Specs anzeigen"
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "SearchResultsView" = self.view  # type: ignore[assignment]
        view.show_specs = not view.show_specs
        view.rebuild_buttons()
        embeds = await view.build_embeds()
        await interaction.response.edit_message(embeds=embeds, view=view)


class SearchEditButton(ui.Button):
    """Erlaubt dem/der Ersteller(in) des Eintrags oder Admins, ihn direkt aus
    den Suchergebnissen heraus zu bearbeiten (Farbe/YouTube-Link/Bilder)."""

    def __init__(self) -> None:
        super().__init__(label="✏️ Bearbeiten", style=discord.ButtonStyle.primary, row=3)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "SearchResultsView" = self.view  # type: ignore[assignment]
        r = view.results[view.index]

        is_owner = interaction.user.id == r.get("ersteller_id")
        is_admin = (
            isinstance(interaction.user, discord.Member)
            and interaction.user.guild_permissions.administrator
        )
        if not (is_owner or is_admin):
            await interaction.response.send_message(
                "❌ Nur die Person, die diesen Eintrag erstellt hat, oder ein Admin kann ihn bearbeiten.",
                ephemeral=True,
            )
            return

        actions_view = EditActionsView(r)
        await interaction.response.send_message(
            f"✏️ Was möchtest du an **{r['name']}** (ID {r['id']}) ändern?",
            view=actions_view,
            ephemeral=True,
        )


class SearchResultsView(ui.View):
    """
    Ergebnisliste mit Zurück/Weiter. Bilder und Farm-Specs sind standardmäßig
    eingeklappt und lassen sich per Button ein-/ausblenden; über den
    Entfernungs-Button kann die Distanz auch nachträglich berechnet werden.
    """

    def __init__(
        self,
        results: List[dict],
        origin: Optional[Tuple[float, float]],
        guild_id: Optional[int] = None,
    ) -> None:
        super().__init__(timeout=180)
        self.results = results
        self.origin = origin
        self.guild_id = guild_id
        self.index = 0
        self.show_images = False
        self.show_specs = False
        self.rebuild_buttons()

    def rebuild_buttons(self) -> None:
        self.clear_items()
        prev_btn = SearchPrevButton()
        next_btn = SearchNextButton()
        prev_btn.disabled = self.index <= 0
        next_btn.disabled = self.index >= len(self.results) - 1
        self.add_item(prev_btn)
        self.add_item(next_btn)

        self.add_item(SearchDistanceButton())
        self.add_item(SearchImagesToggleButton(self.show_images))

        r = self.results[self.index]
        if r.get("specs"):
            self.add_item(SearchSpecsToggleButton(self.show_specs))

        if r.get("forum_thread_id") and self.guild_id:
            url = f"https://discord.com/channels/{self.guild_id}/{r['forum_thread_id']}"
            self.add_item(ui.Button(label="💬 Zum Forum-Beitrag", url=url, row=2))

        if r.get("youtube_link"):
            self.add_item(ui.Button(label="▶️ Tutorial ansehen", url=r["youtube_link"], row=2))

        self.add_item(SearchEditButton())

    async def build_embeds(self) -> List[discord.Embed]:
        r = self.results[self.index]
        coord_str = (
            f"X: {r['x']} | Y: {r['y']} | Z: {r['z']}"
            if r.get("y") is not None
            else f"X: {r['x']} | Z: {r['z']}"
        )
        emoji = _category_emoji(r["typ"])
        color = _resolve_color(r["typ"], r.get("color"))

        embed = discord.Embed(title=f"{emoji} {r['name']}", color=color)
        embed.add_field(name="Kategorie", value=r["typ"], inline=True)
        embed.add_field(name="Koordinaten", value=f"`{coord_str}`", inline=True)
        if self.origin and "distanz" in r:
            embed.add_field(name="Entfernung", value=f"~{r['distanz']:.0f} Blöcke", inline=True)
        if r.get("tags"):
            embed.add_field(name="🏷️ Tags", value=r["tags"], inline=False)
        if r.get("beschreibung"):
            embed.add_field(name="Beschreibung", value=r["beschreibung"], inline=False)
        if self.show_specs and r.get("specs"):
            embed.add_field(name="🔧 Specs", value=r["specs"], inline=False)
        embed.set_footer(
            text=f"Eingetragen von {r.get('ersteller_name', 'Unbekannt')} · ID {r['id']} · "
            f"Treffer {self.index + 1}/{len(self.results)}"
        )

        embeds = [embed]
        if self.show_images:
            images = await db.get_images_full(r["id"])
            if not images:
                embed.add_field(name="🖼️ Bilder", value="Keine Bilder vorhanden.", inline=False)
            else:
                for img in images[:MAX_IMAGE_EMBEDS]:
                    img_embed = discord.Embed(color=color)
                    img_embed.set_image(url=img["url"])
                    if img.get("caption"):
                        img_embed.set_footer(text=img["caption"])
                    embeds.append(img_embed)
        return embeds


class SearchTypeSelect(TypeSelect):
    async def callback(self, interaction: discord.Interaction) -> None:
        source, prompt, all_label = _GROUPS[self.values[0]]
        used = set(await db.get_used_types())
        filtered = [(label, emoji) for label, emoji in source if label in used]

        if not filtered:
            await interaction.response.edit_message(
                content="❌ Für diese Kategorie gibt es noch keine Einträge.", view=None
            )
            return

        items = [(all_label, "__all__", "🗂️")] + [(label, label, emoji) for label, emoji in filtered]
        all_filter = [label for label, _ in filtered]
        view = SearchPagedCategoryView(items, prompt, all_filter=all_filter, all_label=all_label)
        await interaction.response.edit_message(content=view.render_content(), view=view)


class SearchTypeView(ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=120)
        self.add_item(SearchTypeSelect())


class SearchView(ui.View):
    """Persistente View mit dem 'Suchen'-Button (funktioniert auch nach Bot-Neustart)."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @ui.button(label="🔍 Suchen", style=discord.ButtonStyle.blurple, custom_id="search_button")
    async def search_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await interaction.response.send_message(
            "Suchst du eine Struktur, ein Biom, eine Farm oder eine Base?", view=SearchTypeView(), ephemeral=True
        )


# --------------------------------------------------------------------------- #
# Löschen (Admin) - per Suche/Durchklicken statt nur per ID
# --------------------------------------------------------------------------- #

class DeleteSearchModal(ui.Modal, title="Eintrag suchen zum Löschen"):
    suchbegriff = ui.TextInput(
        label="Name (optional, leer = alle in Kategorie)",
        placeholder="z.B. Dorf, Wüste, Iron Farm ...",
        required=False,
        max_length=100,
    )

    def __init__(self, category_filter: Optional[Union[str, List[str]]], display_label: str) -> None:
        super().__init__()
        self.category_filter = category_filter
        self.display_label = display_label
        self.title = f"Löschen: {display_label}"[:45]

    async def on_submit(self, interaction: discord.Interaction) -> None:
        term = self.suchbegriff.value.strip() if self.suchbegriff.value else ""
        results = await db.search_entries(term=term, typ=self.category_filter)

        if not results:
            details = []
            if self.category_filter:
                details.append(f"Kategorie **{self.display_label}**")
            if term:
                details.append(f"Name **{term}**")
            suffix = f" für {' und '.join(details)}" if details else ""
            await interaction.response.send_message(f"❌ Keine Einträge gefunden{suffix}.", ephemeral=True)
            return

        guild_id = interaction.guild.id if interaction.guild else None
        view = DeleteResultsView(results, guild_id=guild_id)
        embeds = await view.build_embeds()
        await interaction.response.send_message(embeds=embeds, view=view, ephemeral=True)


class DeletePrevButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="◀ Zurück", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "DeleteResultsView" = self.view  # type: ignore[assignment]
        view.index -= 1
        view.show_images = False
        view.show_specs = False
        view.rebuild_buttons()
        embeds = await view.build_embeds()
        await interaction.response.edit_message(embeds=embeds, view=view)


class DeleteNextButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="Weiter ▶", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "DeleteResultsView" = self.view  # type: ignore[assignment]
        view.index += 1
        view.show_images = False
        view.show_specs = False
        view.rebuild_buttons()
        embeds = await view.build_embeds()
        await interaction.response.edit_message(embeds=embeds, view=view)


class DeleteImagesToggleButton(ui.Button):
    def __init__(self, shown: bool) -> None:
        label = "🙈 Bilder verbergen" if shown else "🖼️ Bilder anzeigen"
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "DeleteResultsView" = self.view  # type: ignore[assignment]
        view.show_images = not view.show_images
        view.rebuild_buttons()
        embeds = await view.build_embeds()
        await interaction.response.edit_message(embeds=embeds, view=view)


class DeleteSpecsToggleButton(ui.Button):
    def __init__(self, shown: bool) -> None:
        label = "🙈 Specs verbergen" if shown else "🔧 Specs anzeigen"
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "DeleteResultsView" = self.view  # type: ignore[assignment]
        view.show_specs = not view.show_specs
        view.rebuild_buttons()
        embeds = await view.build_embeds()
        await interaction.response.edit_message(embeds=embeds, view=view)


# --------------------------------------------------------------------------- #
# Bearbeiten: Farbe, YouTube-Link, Bilder (hinzufügen/löschen/beschreiben)
# --------------------------------------------------------------------------- #

async def _collect_and_archive_images(
    interaction: discord.Interaction, entry_id: int, user_id: int
) -> List[Dict[str, Any]]:
    """
    Wartet bis zu 3 Minuten auf Bild-Nachrichten im aktuellen Channel (oder bis
    auf "✅ Fertig" geklickt wird), archiviert sie gruppiert im Bild-Archiv-Channel,
    speichert sie in der Datenbank und löscht anschließend die ursprünglichen
    Nachrichten. Liefert die (aktualisierte) vollständige Bilderliste des Eintrags.
    Erwartet, dass die Interaction bereits deferred wurde (ephemeral).
    """
    bot = interaction.client
    finish_view = FinishUploadView(user_id)
    prompt_message = await interaction.followup.send(
        "📸 Sende jetzt bis zu 3 Minuten lang Bild(er) in diesen Channel. Deine "
        "Nachrichten werden danach automatisch gelöscht. Klicke auf **✅ Fertig**, "
        "wenn du keine weiteren Bilder mehr hochladen möchtest.",
        view=finish_view,
        ephemeral=True,
    )

    collected_messages: List[discord.Message] = []
    collected_attachments: List[discord.Attachment] = []

    def check(m: discord.Message) -> bool:
        return m.author.id == user_id and m.channel.id == interaction.channel.id

    loop = asyncio.get_event_loop()
    end_time = loop.time() + 180

    while True:
        remaining = end_time - loop.time()
        if remaining <= 0 or finish_view.done_event.is_set():
            break

        message_task = asyncio.ensure_future(bot.wait_for("message", check=check))
        done_task = asyncio.ensure_future(finish_view.done_event.wait())
        done, pending = await asyncio.wait(
            {message_task, done_task}, timeout=remaining, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

        if not done or done_task in done:
            break

        try:
            msg = message_task.result()
        except Exception:
            break

        image_attachments = [
            att for att in msg.attachments
            if att.content_type and att.content_type.startswith("image/")
        ]
        if image_attachments:
            collected_messages.append(msg)
            collected_attachments.extend(image_attachments)

    finish_view.stop()
    try:
        await prompt_message.edit(content="⏳ Bild-Upload beendet, verarbeite Bilder ...", view=None)
    except discord.HTTPException:
        pass

    saved_urls: List[str] = []
    if collected_attachments and interaction.guild is not None:
        try:
            archive_channel = await _get_image_channel(interaction.guild)
            files = [await att.to_file() for att in collected_attachments]
            for i in range(0, len(files), 10):
                chunk = files[i:i + 10]
                archive_msg = await archive_channel.send(
                    content=(
                        f"Bilder zu Eintrag #{entry_id} (nachträglich hinzugefügt von {interaction.user})"
                        if i == 0
                        else None
                    ),
                    files=chunk,
                )
                saved_urls.extend(att.url for att in archive_msg.attachments)
        except discord.HTTPException:
            pass

    for m in collected_messages:
        try:
            await m.delete()
        except discord.HTTPException:
            pass

    if saved_urls:
        await db.add_images(entry_id, saved_urls)

    return await db.get_images_full(entry_id)


class ImageManagePrevButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="◀", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ImageManageView" = self.view  # type: ignore[assignment]
        view.index -= 1
        view.rebuild_buttons()
        await interaction.response.edit_message(
            content=view.render_content(), embed=view.build_embed(), view=view
        )


class ImageManageNextButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="▶", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ImageManageView" = self.view  # type: ignore[assignment]
        view.index += 1
        view.rebuild_buttons()
        await interaction.response.edit_message(
            content=view.render_content(), embed=view.build_embed(), view=view
        )


class ImageManageCaptionModal(ui.Modal, title="Bildbeschreibung ändern"):
    def __init__(self, gallery: "ImageManageView", image_id: int, current: Optional[str]) -> None:
        super().__init__()
        self.gallery = gallery
        self.image_id = image_id
        self.beschreibung = ui.TextInput(
            label="Beschreibung (leer lassen zum Entfernen)",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=200,
            default=current or None,
        )
        self.add_item(self.beschreibung)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        caption = self.beschreibung.value.strip() if self.beschreibung.value else ""
        await db.set_image_caption(self.image_id, caption)
        for img in self.gallery.images:
            if img["id"] == self.image_id:
                img["caption"] = caption
        await interaction.response.edit_message(
            content=self.gallery.render_content(), embed=self.gallery.build_embed(), view=self.gallery
        )
        await _sync_forum_post(interaction.guild, self.gallery.entry_id)


class ImageManageCaptionButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="✏️ Beschreibung ändern", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ImageManageView" = self.view  # type: ignore[assignment]
        if not view.images:
            await interaction.response.defer()
            return
        img = view.images[view.index]
        await interaction.response.send_modal(
            ImageManageCaptionModal(view, img["id"], img.get("caption"))
        )


class ImageManageDeleteButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="🗑️ Bild löschen", style=discord.ButtonStyle.danger, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ImageManageView" = self.view  # type: ignore[assignment]
        if not view.images:
            await interaction.response.defer()
            return
        img = view.images.pop(view.index)
        await db.delete_image(img["id"])
        if view.index >= len(view.images) and view.index > 0:
            view.index -= 1
        view.rebuild_buttons()
        await interaction.response.edit_message(
            content=view.render_content(), embed=view.build_embed(), view=view
        )
        await _sync_forum_post(interaction.guild, view.entry_id)


class ImageManageAddButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="➕ Bild hinzufügen", style=discord.ButtonStyle.success, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "ImageManageView" = self.view  # type: ignore[assignment]
        await interaction.response.defer(ephemeral=True)
        new_images = await _collect_and_archive_images(interaction, view.entry_id, interaction.user.id)
        view.images = new_images
        view.index = max(0, len(view.images) - 1)
        view.rebuild_buttons()
        await interaction.followup.send(
            content=view.render_content(), embed=view.build_embed(), view=view, ephemeral=True
        )
        await _sync_forum_post(interaction.guild, view.entry_id)


class ImageManageView(ui.View):
    """Galerie zum Verwalten der Bilder eines bestehenden Eintrags (Beschreiben,
    Löschen, Hinzufügen)."""

    def __init__(self, entry_id: int, images: List[Dict[str, Any]]) -> None:
        super().__init__(timeout=300)
        self.entry_id = entry_id
        self.images = images
        self.index = max(0, len(images) - 1) if images else 0
        self.rebuild_buttons()

    def rebuild_buttons(self) -> None:
        self.clear_items()
        prev_btn = ImageManagePrevButton()
        next_btn = ImageManageNextButton()
        prev_btn.disabled = not self.images or self.index <= 0
        next_btn.disabled = not self.images or self.index >= len(self.images) - 1
        self.add_item(prev_btn)
        self.add_item(next_btn)

        caption_btn = ImageManageCaptionButton()
        delete_btn = ImageManageDeleteButton()
        caption_btn.disabled = not self.images
        delete_btn.disabled = not self.images
        self.add_item(caption_btn)
        self.add_item(delete_btn)

        self.add_item(ImageManageAddButton())

    def render_content(self) -> str:
        if not self.images:
            return "Für diesen Eintrag sind aktuell keine Bilder hinterlegt."
        return f"Bild {self.index + 1} von {len(self.images)}"

    def build_embed(self) -> Optional[discord.Embed]:
        if not self.images:
            return None
        img = self.images[self.index]
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_image(url=img["url"])
        embed.description = img.get("caption") or "_Keine Beschreibung._"
        return embed


class EditYoutubeLinkModal(ui.Modal, title="YouTube-Link ändern"):
    def __init__(self, entry_id: int, current: Optional[str]) -> None:
        super().__init__()
        self.entry_id = entry_id
        self.youtube_link = ui.TextInput(
            label="YouTube-Link (leer lassen zum Entfernen)",
            placeholder="z.B. https://youtu.be/...",
            required=False,
            max_length=200,
            default=current or None,
        )
        self.add_item(self.youtube_link)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        link = self.youtube_link.value.strip() if self.youtube_link.value else None
        if link and "youtu" not in link.lower():
            await interaction.response.send_message(
                "❌ Das sieht nicht nach einem YouTube-Link aus. Bitte einen gültigen Link "
                "angeben oder das Feld leer lassen.",
                ephemeral=True,
            )
            return
        await db.set_entry_youtube(self.entry_id, link)
        text = f"✅ YouTube-Link aktualisiert: {link}" if link else "✅ YouTube-Link entfernt."
        await interaction.response.edit_message(content=text, view=None)
        await _sync_forum_post(interaction.guild, self.entry_id)


class EditDetailsButton(ui.Button):
    def __init__(self, entry: Dict[str, Any]) -> None:
        super().__init__(label="📝 Details (Name/Koordinaten/...)", style=discord.ButtonStyle.secondary, row=0)
        self.entry = entry

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(ForumEditModal(self.entry))


class EditColorButton(ui.Button):
    def __init__(self, entry_id: int) -> None:
        super().__init__(label="🎨 Farbe ändern", style=discord.ButtonStyle.secondary, row=0)
        self.entry_id = entry_id

    async def callback(self, interaction: discord.Interaction) -> None:
        color_view = ColorView(self.entry_id)
        await interaction.response.edit_message(
            content="🎨 Wähle eine neue Embed-Farbe für diesen Eintrag:", view=color_view
        )


class EditYoutubeButton(ui.Button):
    def __init__(self, entry_id: int, current_link: Optional[str]) -> None:
        super().__init__(label="🔗 YouTube-Link ändern", style=discord.ButtonStyle.secondary, row=1)
        self.entry_id = entry_id
        self.current_link = current_link

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(EditYoutubeLinkModal(self.entry_id, self.current_link))


class EditImagesButton(ui.Button):
    def __init__(self, entry_id: int) -> None:
        super().__init__(label="🖼️ Bilder verwalten", style=discord.ButtonStyle.secondary, row=1)
        self.entry_id = entry_id

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        images = await db.get_images_full(self.entry_id)
        gallery = ImageManageView(self.entry_id, images)
        await interaction.followup.send(
            content=gallery.render_content(), embed=gallery.build_embed(), view=gallery, ephemeral=True
        )


class EditActionsView(ui.View):
    """
    Zentrales Bearbeiten-Menü für einen Eintrag: Name/Koordinaten/Beschreibung/
    Specs, Farbe, YouTube-Link und Bilder (inkl. Beschreibungen). Wird sowohl vom
    persistenten Forum-Bearbeiten-Button als auch aus Suchen/Löschen heraus genutzt.
    """

    def __init__(self, entry: Dict[str, Any]) -> None:
        super().__init__(timeout=300)
        self.add_item(EditDetailsButton(entry))
        self.add_item(EditColorButton(entry["id"]))
        if entry.get("typ") in _FARM_LABELS:
            self.add_item(EditYoutubeButton(entry["id"], entry.get("youtube_link")))
        self.add_item(EditImagesButton(entry["id"]))


class EditEntryButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="✏️ Bearbeiten", style=discord.ButtonStyle.primary, row=3)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "DeleteResultsView" = self.view  # type: ignore[assignment]
        if not view.results:
            await interaction.response.defer()
            return
        entry = view.results[view.index]
        actions_view = EditActionsView(entry)
        await interaction.response.send_message(
            f"✏️ Was möchtest du an **{entry['name']}** (ID {entry['id']}) ändern?",
            view=actions_view,
            ephemeral=True,
        )


class DeleteConfirmButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="🗑️ Diesen Eintrag löschen", style=discord.ButtonStyle.danger, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "DeleteResultsView" = self.view  # type: ignore[assignment]
        if not view.results:
            await interaction.response.defer()
            return

        entry = view.results.pop(view.index)
        await db.delete_entry(entry["id"])
        await _delete_forum_post(interaction.guild, entry.get("forum_thread_id"))

        if view.index >= len(view.results) and view.index > 0:
            view.index -= 1
        view.show_images = False
        view.show_specs = False
        view.rebuild_buttons()

        embeds = await view.build_embeds()
        await interaction.response.edit_message(
            content=f"🗑️ **{entry['name']}** (ID {entry['id']}) wurde gelöscht.", embeds=embeds, view=view
        )

        await log_action(
            interaction.guild,
            discord.Embed(
                title="🗑️ Eintrag gelöscht",
                description=(
                    f"{_category_emoji(entry['typ'])} **{entry['name']}** ({entry['typ']}) ID `{entry['id']}`\n"
                    f"Gelöscht von: {interaction.user.mention}"
                ),
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            ),
        )


class DeleteResultsView(ui.View):
    """Zum Durchklicken der Treffer mit ein-/ausklappbaren Bildern/Specs und Lösch-Button."""

    def __init__(self, results: List[dict], guild_id: Optional[int] = None) -> None:
        super().__init__(timeout=180)
        self.results = results
        self.guild_id = guild_id
        self.index = 0
        self.show_images = False
        self.show_specs = False
        self.rebuild_buttons()

    def rebuild_buttons(self) -> None:
        self.clear_items()
        prev_btn = DeletePrevButton()
        next_btn = DeleteNextButton()
        prev_btn.disabled = self.index <= 0
        next_btn.disabled = not self.results or self.index >= len(self.results) - 1
        self.add_item(prev_btn)
        self.add_item(next_btn)

        if self.results:
            self.add_item(DeleteImagesToggleButton(self.show_images))
            r = self.results[self.index]
            if r.get("specs"):
                self.add_item(DeleteSpecsToggleButton(self.show_specs))
            if r.get("forum_thread_id") and self.guild_id:
                url = f"https://discord.com/channels/{self.guild_id}/{r['forum_thread_id']}"
                self.add_item(ui.Button(label="💬 Zum Forum-Beitrag", url=url, row=2))
            if r.get("youtube_link"):
                self.add_item(ui.Button(label="▶️ Tutorial ansehen", url=r["youtube_link"], row=2))

        edit_btn = EditEntryButton()
        edit_btn.disabled = not self.results
        edit_btn.row = 3
        self.add_item(edit_btn)

        delete_btn = DeleteConfirmButton()
        delete_btn.disabled = not self.results
        delete_btn.row = 3
        self.add_item(delete_btn)

    async def build_embeds(self) -> List[discord.Embed]:
        if not self.results:
            return [
                discord.Embed(
                    title="Keine Einträge mehr",
                    description="Es gibt keine (weiteren) Einträge in dieser Auswahl.",
                    color=discord.Color.dark_grey(),
                )
            ]

        r = self.results[self.index]
        coord_str = (
            f"X: {r['x']} | Y: {r['y']} | Z: {r['z']}"
            if r.get("y") is not None
            else f"X: {r['x']} | Z: {r['z']}"
        )
        emoji = _category_emoji(r["typ"])

        embed = discord.Embed(title=f"🗑️ {emoji} {r['name']}", color=discord.Color.red())
        embed.add_field(name="Kategorie", value=r["typ"], inline=True)
        embed.add_field(name="Koordinaten", value=f"`{coord_str}`", inline=True)
        embed.add_field(name="ID", value=f"`{r['id']}`", inline=True)
        if r.get("tags"):
            embed.add_field(name="🏷️ Tags", value=r["tags"], inline=False)
        if r.get("beschreibung"):
            embed.add_field(name="Beschreibung", value=r["beschreibung"], inline=False)
        if self.show_specs and r.get("specs"):
            embed.add_field(name="🔧 Specs", value=r["specs"], inline=False)
        embed.set_footer(
            text=f"Eingetragen von {r.get('ersteller_name', 'Unbekannt')} · "
            f"Eintrag {self.index + 1}/{len(self.results)}"
        )

        embeds = [embed]
        if self.show_images:
            images = await db.get_images_full(r["id"])
            if not images:
                embed.add_field(name="🖼️ Bilder", value="Keine Bilder vorhanden.", inline=False)
            else:
                for img in images[:MAX_IMAGE_EMBEDS]:
                    img_embed = discord.Embed(color=discord.Color.red())
                    img_embed.set_image(url=img["url"])
                    if img.get("caption"):
                        img_embed.set_footer(text=img["caption"])
                    embeds.append(img_embed)
        return embeds


class DeleteTypeSelect(TypeSelect):
    async def callback(self, interaction: discord.Interaction) -> None:
        source, prompt, all_label = _GROUPS[self.values[0]]
        used = set(await db.get_used_types())
        filtered = [(label, emoji) for label, emoji in source if label in used]

        if not filtered:
            await interaction.response.edit_message(
                content="❌ Für diese Kategorie gibt es noch keine Einträge.", view=None
            )
            return

        items = [(all_label, "__all__", "🗂️")] + [(label, label, emoji) for label, emoji in filtered]
        all_filter = [label for label, _ in filtered]
        view = DeletePagedCategoryView(items, prompt, all_filter=all_filter, all_label=all_label)
        await interaction.response.edit_message(content=view.render_content(), view=view)


class DeleteTypeView(ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=120)
        self.add_item(DeleteTypeSelect())