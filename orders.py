"""
Farm-Bestellungen & Aufträge: Nutzer können anfragen, dass jemand für sie etwas
farmt (Bestellung, z.B. "5 Stacks Eisen") oder etwas anderes erledigt (Auftrag,
z.B. "einen Weg bauen"). Eigenständiges System, unabhängig von den
Struktur/Biom/Farm/Base-Einträgen.

Ablauf: Button "📋 Bestellung/Auftrag aufgeben" -> Auswahl Bestellung oder Auftrag
-> Modal (Titel passt sich an: "Was soll gefarmt werden?" bzw. "Was soll gemacht
werden?", plus Beschreibung) -> Dringlichkeit (Dropdown, wird als echter Forum-Tag
angewendet) -> optional mehrere Personen pingen -> optional ein YouTube-Video
verlinken -> optional Bilder hochladen -> Forum-Beitrag wird erstellt, bekommt
automatisch den Tag "Offen" sowie die Dringlichkeits-Tag und zwei Buttons:

- "🔧 In Bearbeitung": merkt sich, wer die Bestellung/den Auftrag übernommen hat
  (wird im Beitrag angezeigt), der Tag wechselt von "Offen" auf "In Bearbeitung".
- "✅ Fertig": fragt optional nach einem Bild, wo die Kiste mit den Items steht,
  setzt den Status auf "Erledigt" (Tag wechselt entsprechend) und pingt die Person,
  die die Bestellung/den Auftrag ursprünglich aufgegeben hat, im Forum-Beitrag.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

import discord
from discord import ui

import database as db
from logs import log_action
from views import FinishUploadView, _get_image_channel, _resolve_forum_tags

# Bestellung (Items farmen) vs. Auftrag (alles andere, z.B. "einen Weg bauen").
ORDER_TYPE_INFO: Dict[str, Dict[str, str]] = {
    "bestellung": {
        "emoji": "📦",
        "label": "Bestellung",
        "button_label": "📦 Bestellung (Items farmen)",
        "item_label": "Was soll gefarmt werden?",
        "item_placeholder": "z.B. 5 Stacks Eisen, 2 Shulker Gold, 64 Netherit-Schrott ...",
        "modal_title": "Farm-Bestellung aufgeben",
    },
    "auftrag": {
        "emoji": "🛠️",
        "label": "Auftrag",
        "button_label": "🛠️ Auftrag (z.B. etwas bauen)",
        "item_label": "Was soll gemacht werden?",
        "item_placeholder": "z.B. einen Weg zur Farm bauen, eine Brücke, Redstone verkabeln ...",
        "modal_title": "Auftrag aufgeben",
    },
}

# Vorgeschlagene Dringlichkeits-Stufen (werden als echte Discord-Forum-Tags
# angewendet, zusätzlich zum Status-Tag Offen/In Bearbeitung/Erledigt).
URGENCY_LEVELS: List[Tuple[str, str]] = [
    ("Niedrig", "🟢"),
    ("Mittel", "🟡"),
    ("Hoch", "🟠"),
    ("Dringend", "🔴"),
]
_URGENCY_EMOJI: Dict[str, str] = {name: emoji for name, emoji in URGENCY_LEVELS}

# Status -> Anzeige-Text/Emoji und Name des Forum-Tags.
STATUS_INFO: Dict[str, Tuple[str, str]] = {
    "offen": ("🟩 Offen", "Offen"),
    "in_bearbeitung": ("🔧 In Bearbeitung", "In Bearbeitung"),
    "erledigt": ("✅ Erledigt", "Erledigt"),
}


def _urgency_color(urgency: Optional[str]) -> discord.Color:
    return {
        "Niedrig": discord.Color.green(),
        "Mittel": discord.Color.gold(),
        "Hoch": discord.Color.orange(),
        "Dringend": discord.Color.red(),
    }.get(urgency or "", discord.Color.blurple())


def _order_type_info(order: Dict[str, Any]) -> Dict[str, str]:
    return ORDER_TYPE_INFO.get(order.get("order_type") or "bestellung", ORDER_TYPE_INFO["bestellung"])


def _parse_ping_ids(order: Dict[str, Any]) -> List[int]:
    raw = order.get("ping_user_ids")
    if not raw:
        return []
    return [int(x) for x in raw.split(",") if x.strip().isdigit()]


def _parse_ping_role_ids(order: Dict[str, Any]) -> List[int]:
    raw = order.get("ping_role_ids")
    if not raw:
        return []
    return [int(x) for x in raw.split(",") if x.strip().isdigit()]


async def _get_orders_forum_channel(guild: Optional[discord.Guild]) -> Optional[discord.ForumChannel]:
    if guild is None:
        return None
    channel_id = await db.get_config("bestellungen_forum_channel_id")
    if not channel_id:
        return None
    channel = guild.get_channel(int(channel_id))
    return channel if isinstance(channel, discord.ForumChannel) else None


async def _get_order_thread(guild: Optional[discord.Guild], thread_id: Optional[int]) -> Optional[discord.Thread]:
    if guild is None or not thread_id:
        return None
    try:
        thread = guild.get_channel_or_thread(thread_id)
        if thread is None:
            thread = await guild.fetch_channel(thread_id)
        return thread if isinstance(thread, discord.Thread) else None
    except discord.HTTPException:
        return None


async def _build_order_embeds(order: Dict[str, Any], images: List[Dict[str, Any]]) -> List[discord.Embed]:
    color = _urgency_color(order.get("urgency"))
    status_label, _ = STATUS_INFO.get(order.get("status") or "offen", STATUS_INFO["offen"])
    type_info = _order_type_info(order)

    main = discord.Embed(
        title=f"{type_info['emoji']} {order['item']}", color=color, timestamp=discord.utils.utcnow()
    )
    main.add_field(name="Art", value=type_info["label"], inline=True)
    if order.get("urgency"):
        emoji = _URGENCY_EMOJI.get(order["urgency"], "")
        main.add_field(name="Dringlichkeit", value=f"{emoji} {order['urgency']}", inline=True)
    main.add_field(name="Status", value=status_label, inline=True)
    main.add_field(name="ID", value=f"`{order['id']}`", inline=True)
    if order.get("beschreibung"):
        main.add_field(name="Beschreibung", value=order["beschreibung"], inline=False)
    if order.get("youtube_link"):
        main.add_field(name="▶️ Video", value=order["youtube_link"], inline=False)

    ping_ids = _parse_ping_ids(order)
    role_ping_ids = _parse_ping_role_ids(order)
    ping_mentions = [f"<@{uid}>" for uid in ping_ids] + [f"<@&{rid}>" for rid in role_ping_ids]
    if ping_mentions:
        main.add_field(name="Für", value=" ".join(ping_mentions), inline=False)

    if order.get("claimed_by_name"):
        main.add_field(name="🙋 Übernommen von", value=order["claimed_by_name"], inline=False)

    main.set_footer(text=f"Aufgegeben von {order.get('ersteller_name', 'Unbekannt')}")

    embeds = [main]
    request_images = [i for i in images if i.get("kind") == "request"]
    delivery_images = [i for i in images if i.get("kind") == "delivery"]

    for img in request_images[:6]:
        e = discord.Embed(color=color)
        e.set_image(url=img["url"])
        if img.get("caption"):
            e.set_footer(text=img["caption"])
        embeds.append(e)

    if delivery_images:
        note = discord.Embed(
            title="📍 Abgabe-Ort", description="Hier steht die Kiste mit den Items:", color=discord.Color.green()
        )
        embeds.append(note)
        for img in delivery_images[:2]:
            e = discord.Embed(color=discord.Color.green())
            e.set_image(url=img["url"])
            embeds.append(e)

    return embeds[:10]


async def _order_tags(order: Dict[str, Any]) -> List[str]:
    tags = [_order_type_info(order)["label"]]
    if order.get("urgency"):
        tags.append(order["urgency"])
    _, tag_name = STATUS_INFO.get(order.get("status") or "offen", STATUS_INFO["offen"])
    tags.append(tag_name)
    return tags


async def _sync_order_forum_post(guild: Optional[discord.Guild], order_id: int) -> None:
    """Aktualisiert Embeds und Status-/Dringlichkeits-Tags des Forum-Beitrags neu."""
    order = await db.get_order(order_id)
    if not order or not order.get("forum_thread_id"):
        return

    thread = await _get_order_thread(guild, order["forum_thread_id"])
    if thread is None:
        return

    images = await db.get_order_images(order_id)
    embeds = await _build_order_embeds(order, images)
    try:
        starter_message = await thread.fetch_message(thread.id)
        await starter_message.edit(embeds=embeds)
    except discord.HTTPException:
        pass

    channel = thread.parent
    if isinstance(channel, discord.ForumChannel):
        tag_names = await _order_tags(order)
        applied_tags = await _resolve_forum_tags(channel, tag_names)
        try:
            await thread.edit(applied_tags=applied_tags)
        except discord.HTTPException:
            pass


async def _create_order_forum_post(guild: Optional[discord.Guild], order_id: int) -> None:
    """Erstellt den Forum-Beitrag für eine neue Bestellung/einen neuen Auftrag,
    inkl. Status-Tag "Offen" und Dringlichkeits-Tag, sowie den Buttons
    "🔧 In Bearbeitung" und "✅ Fertig"."""
    if guild is None:
        return
    order = await db.get_order(order_id)
    if not order:
        return

    channel = await _get_orders_forum_channel(guild)
    if channel is None:
        print(
            f"[Bestellungen-Forum] Kein Forum-Channel konfiguriert (Config-Key "
            f"'bestellungen_forum_channel_id' ist leer oder Channel nicht gefunden) - "
            f"Bestellung #{order_id} bekommt keinen Forum-Beitrag."
        )
        return

    images = await db.get_order_images(order_id)
    embeds = await _build_order_embeds(order, images)
    tag_names = await _order_tags(order)
    applied_tags = await _resolve_forum_tags(channel, tag_names)

    view = discord.ui.View(timeout=None)
    view.add_item(OrderProgressButton(order_id))
    view.add_item(OrderDoneButton(order_id))

    ping_ids = _parse_ping_ids(order)
    role_ping_ids = _parse_ping_role_ids(order)
    mentions = [f"<@{uid}>" for uid in ping_ids] + [f"<@&{rid}>" for rid in role_ping_ids]
    content = " ".join(mentions) if mentions else None

    try:
        result = await channel.create_thread(
            name=order["item"][:100], content=content, embeds=embeds, applied_tags=applied_tags, view=view
        )
        await db.set_order_forum_thread(order_id, result.thread.id)
    except discord.HTTPException as e:
        print(f"[Bestellungen-Forum] Erstellen des Forum-Beitrags für Bestellung #{order_id} fehlgeschlagen: {e}")


async def _collect_order_images(
    interaction: discord.Interaction,
    order_id: int,
    finish_view: "FinishUploadView",
    prompt_message: discord.Message,
    user_id: int,
    kind: str,
) -> List[str]:
    """
    Wartet bis zu 3 Minuten auf Bild-Nachrichten im aktuellen Channel (oder bis auf
    "✅ Fertig" geklickt wird), archiviert sie gruppiert im Bild-Archiv-Channel,
    speichert sie zur Bestellung und löscht die ursprünglichen Nachrichten danach.
    """
    bot = interaction.client
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
                        f"Bild(er) zu Bestellung #{order_id} ({kind}, von {interaction.user})"
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
        await db.add_order_images(order_id, saved_urls, kind)

    return saved_urls


# --------------------------------------------------------------------------- #
# Schritt 0: Bestellung oder Auftrag?
# --------------------------------------------------------------------------- #

class OrderTypeButton(ui.Button):
    def __init__(self, order_type: str) -> None:
        info = ORDER_TYPE_INFO[order_type]
        super().__init__(label=info["button_label"], style=discord.ButtonStyle.primary)
        self.order_type = order_type

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(OrderModal(self.order_type))


class OrderTypeView(ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=180)
        self.add_item(OrderTypeButton("bestellung"))
        self.add_item(OrderTypeButton("auftrag"))


# --------------------------------------------------------------------------- #
# Bestellung/Auftrag aufgeben: Modal -> Dringlichkeit -> Ping -> YouTube -> Bilder
# --------------------------------------------------------------------------- #

class OrderModal(ui.Modal):
    def __init__(self, order_type: str) -> None:
        self.order_type = order_type
        info = ORDER_TYPE_INFO[order_type]
        super().__init__(title=info["modal_title"])

        self.item = ui.TextInput(
            label=info["item_label"], placeholder=info["item_placeholder"], max_length=100
        )
        self.beschreibung = ui.TextInput(
            label="Beschreibung (optional)",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500,
        )
        self.add_item(self.item)
        self.add_item(self.beschreibung)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        info = ORDER_TYPE_INFO[self.order_type]
        order_id = await db.add_order(
            item=self.item.value.strip(),
            beschreibung=self.beschreibung.value.strip() if self.beschreibung.value else None,
            ersteller_id=interaction.user.id,
            ersteller_name=str(interaction.user),
            order_type=self.order_type,
        )

        embed = discord.Embed(
            title=f"{info['emoji']} {self.item.value.strip()}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Art", value=info["label"], inline=True)
        embed.add_field(name="ID", value=f"`{order_id}`", inline=True)
        if self.beschreibung.value:
            embed.add_field(name="Beschreibung", value=self.beschreibung.value, inline=False)
        embed.set_footer(
            text=f"Aufgegeben von {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(
            content=f"✅ {info['label']} erstellt!", embed=embed, ephemeral=True
        )

        await log_action(
            interaction.guild,
            discord.Embed(
                title=f"{info['emoji']} Neue {info['label']}",
                description=f"**{self.item.value.strip()}** · ID `{order_id}`\nVon: {interaction.user.mention}",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow(),
            ),
        )

        urgency_view = UrgencyView(order_id)
        await interaction.followup.send(urgency_view.render_content(), view=urgency_view, ephemeral=True)


class UrgencySelect(ui.Select):
    def __init__(self, selected: Optional[str]) -> None:
        options = [
            discord.SelectOption(label=name, value=name, emoji=emoji, default=(name == selected))
            for name, emoji in URGENCY_LEVELS
        ]
        super().__init__(placeholder="Dringlichkeit auswählen", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "UrgencyView" = self.view  # type: ignore[assignment]
        view.urgency = self.values[0]
        await db.set_order_urgency(view.order_id, view.urgency)
        view.rebuild_buttons()
        await interaction.response.edit_message(content=view.render_content(), view=view)


class UrgencyNextButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="➡️ Weiter (Personen pingen)", style=discord.ButtonStyle.success, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "UrgencyView" = self.view  # type: ignore[assignment]
        ping_view = PingUserView(view.order_id)
        await interaction.response.edit_message(content=ping_view.render_content(), view=ping_view)


class UrgencyView(ui.View):
    def __init__(self, order_id: int) -> None:
        super().__init__(timeout=300)
        self.order_id = order_id
        self.urgency: Optional[str] = None
        self.rebuild_buttons()

    def rebuild_buttons(self) -> None:
        self.clear_items()
        self.add_item(UrgencySelect(self.urgency))
        self.add_item(UrgencyNextButton())

    def render_content(self) -> str:
        current = self.urgency or "_noch nicht gewählt_"
        return f"🚦 Wie dringend ist es?\n**Aktuell:** {current}"


class PingUserSelect(ui.MentionableSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Optional: bis zu 10 Personen und/oder Rollen pingen",
            min_values=0,
            max_values=10,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "PingUserView" = self.view  # type: ignore[assignment]
        view.ping_users = [v for v in self.values if isinstance(v, (discord.Member, discord.User))]
        view.ping_roles = [v for v in self.values if isinstance(v, discord.Role)]
        await db.set_order_ping_users(view.order_id, [u.id for u in view.ping_users])
        await db.set_order_ping_roles(view.order_id, [r.id for r in view.ping_roles])
        view.rebuild_buttons()
        await interaction.response.edit_message(content=view.render_content(), view=view)


class PingUserNextButton(ui.Button):
    def __init__(self) -> None:
        super().__init__(label="➡️ Weiter (YouTube-Video)", style=discord.ButtonStyle.success, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "PingUserView" = self.view  # type: ignore[assignment]
        await interaction.response.send_modal(OrderYoutubeModal(view.order_id))


class PingUserView(ui.View):
    def __init__(self, order_id: int) -> None:
        super().__init__(timeout=300)
        self.order_id = order_id
        self.ping_users: List[discord.abc.User] = []
        self.ping_roles: List[discord.Role] = []
        self.rebuild_buttons()

    def rebuild_buttons(self) -> None:
        self.clear_items()
        self.add_item(PingUserSelect())
        self.add_item(PingUserNextButton())

    def render_content(self) -> str:
        mentions = [u.mention for u in self.ping_users] + [r.mention for r in self.ping_roles]
        current = ", ".join(mentions) if mentions else "_niemand_"
        return f"📣 Möchtest du Personen und/oder Rollen dafür pingen?\n**Aktuell:** {current}"


class OrderYoutubeModal(ui.Modal, title="YouTube-Video verlinken"):
    youtube_link = ui.TextInput(
        label="YouTube-Link (optional)",
        placeholder="z.B. ein Tutorial, wie/wo man das Item bekommt",
        required=False,
        max_length=200,
    )

    def __init__(self, order_id: int) -> None:
        super().__init__()
        self.order_id = order_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        link = self.youtube_link.value.strip() if self.youtube_link.value else None
        if link and "youtu" not in link.lower():
            await interaction.response.send_message(
                "❌ Das sieht nicht nach einem YouTube-Link aus. Bitte einen gültigen Link "
                "angeben oder das Feld leer lassen.",
                ephemeral=True,
            )
            return
        await db.set_order_youtube(self.order_id, link)

        await interaction.response.edit_message(
            content=(f"✅ YouTube-Link gespeichert: {link}" if link else "✅ Kein YouTube-Link hinterlegt."),
            view=None,
        )

        finish_view = FinishUploadView(interaction.user.id)
        prompt_message = await interaction.followup.send(
            "📸 Du kannst jetzt bis zu 3 Minuten lang Bild(er) senden (z.B. ein Bild des "
            "gewünschten Items). Deine Nachrichten werden danach automatisch gelöscht. "
            "Klicke auf **✅ Fertig**, wenn du keine weiteren Bilder hochladen möchtest.",
            view=finish_view,
            ephemeral=True,
        )

        saved_urls = await _collect_order_images(
            interaction, self.order_id, finish_view, prompt_message, interaction.user.id, kind="request"
        )
        await interaction.followup.send(
            f"🖼️ {len(saved_urls)} Bild(er) gespeichert." if saved_urls else "ℹ️ Kein Bild hochgeladen.",
            ephemeral=True,
        )

        await _create_order_forum_post(interaction.guild, self.order_id)


# --------------------------------------------------------------------------- #
# Persistente Buttons im Forum-Beitrag: In Bearbeitung / Fertig
# --------------------------------------------------------------------------- #

class OrderProgressButton(
    discord.ui.DynamicItem[discord.ui.Button], template=r"order_progress:(?P<order_id>\d+)"
):
    def __init__(self, order_id: int) -> None:
        super().__init__(
            discord.ui.Button(
                label="🔧 In Bearbeitung",
                style=discord.ButtonStyle.primary,
                custom_id=f"order_progress:{order_id}",
            )
        )
        self.order_id = order_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: discord.ui.Button, match: "re.Match[str]"
    ) -> "OrderProgressButton":
        return cls(int(match["order_id"]))

    async def callback(self, interaction: discord.Interaction) -> None:
        order = await db.get_order(self.order_id)
        if not order:
            await interaction.response.send_message("❌ Das existiert nicht mehr.", ephemeral=True)
            return
        if order.get("status") == "erledigt":
            await interaction.response.send_message("ℹ️ Das ist bereits als erledigt markiert.", ephemeral=True)
            return

        already_claimed_by = order.get("claimed_by_name")

        await db.set_order_status(self.order_id, "in_bearbeitung")
        await db.set_order_claimed(self.order_id, interaction.user.id, str(interaction.user))

        note = (
            f"\nℹ️ War zuvor bereits von **{already_claimed_by}** übernommen - jetzt auf dich aktualisiert."
            if already_claimed_by and already_claimed_by != str(interaction.user)
            else ""
        )
        await interaction.response.send_message(
            f"🔧 **{order['item']}** ist jetzt als \"In Bearbeitung\" markiert und dir zugeordnet - "
            f"danke, dass du dich kümmerst!{note}",
            ephemeral=True,
        )
        await _sync_order_forum_post(interaction.guild, self.order_id)


class OrderDoneButton(
    discord.ui.DynamicItem[discord.ui.Button], template=r"order_done:(?P<order_id>\d+)"
):
    def __init__(self, order_id: int) -> None:
        super().__init__(
            discord.ui.Button(
                label="✅ Fertig",
                style=discord.ButtonStyle.success,
                custom_id=f"order_done:{order_id}",
            )
        )
        self.order_id = order_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: discord.ui.Button, match: "re.Match[str]"
    ) -> "OrderDoneButton":
        return cls(int(match["order_id"]))

    async def callback(self, interaction: discord.Interaction) -> None:
        order = await db.get_order(self.order_id)
        if not order:
            await interaction.response.send_message("❌ Das existiert nicht mehr.", ephemeral=True)
            return
        if order.get("status") == "erledigt":
            await interaction.response.send_message("ℹ️ Das ist bereits als erledigt markiert.", ephemeral=True)
            return

        # Wer auf "Fertig" klickt, hat es faktisch übernommen/erledigt - falls noch
        # niemand als "übernommen" markiert war, jetzt eintragen.
        if not order.get("claimed_by_id"):
            await db.set_order_claimed(self.order_id, interaction.user.id, str(interaction.user))

        finish_view = FinishUploadView(interaction.user.id)
        await interaction.response.send_message(
            "📸 Optional: Du kannst jetzt bis zu 3 Minuten lang ein Bild senden, wo die Kiste mit "
            "den Items steht. Klicke auf **✅ Fertig**, wenn du kein Bild hochladen möchtest.",
            view=finish_view,
            ephemeral=True,
        )
        prompt_message = await interaction.original_response()

        await _collect_order_images(
            interaction, self.order_id, finish_view, prompt_message, interaction.user.id, kind="delivery"
        )

        await db.set_order_status(self.order_id, "erledigt")
        await _sync_order_forum_post(interaction.guild, self.order_id)

        # Ersteller im Forum-Beitrag pingen, damit er/sie merkt, dass alles fertig ist.
        thread = await _get_order_thread(interaction.guild, order.get("forum_thread_id"))
        if thread is not None:
            try:
                await thread.send(
                    f"<@{order['ersteller_id']}> ✅ Deine Bestellung/dein Auftrag **{order['item']}** "
                    f"wurde von {interaction.user.mention} erledigt!"
                )
            except discord.HTTPException:
                pass

        await interaction.followup.send(
            "✅ Danke! Als erledigt markiert und der/die Erstellende wurde im Forum-Beitrag gepingt.",
            ephemeral=True,
        )


# --------------------------------------------------------------------------- #
# Persistenter "Bestellung/Auftrag aufgeben"-Button für den Bestellungen-Channel
# --------------------------------------------------------------------------- #

class BestellungView(ui.View):
    """Persistente View mit dem 'Bestellung/Auftrag aufgeben'-Button (funktioniert
    auch nach Bot-Neustart)."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @ui.button(
        label="📋 Bestellung/Auftrag aufgeben", style=discord.ButtonStyle.green, custom_id="bestellung_button"
    )
    async def bestellung_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await interaction.response.send_message(
            "Möchtest du eine **Bestellung** (Items farmen) oder einen **Auftrag** "
            "(z.B. etwas bauen) aufgeben?",
            view=OrderTypeView(),
            ephemeral=True,
        )