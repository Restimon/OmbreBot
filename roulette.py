import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import json
import os
import data
from datetime import datetime, timedelta

DATA_FILE = "roulette_data.json"
ALL_CLASSES = [
    "Iop", "Cra", "Eniripsa", "Feca", "Sacrieur", "Xelor",
    "Ecaflip", "Sadida", "Osamodas", "Sram", "Pandawa", "Enutrof",
    "Roublard", "Zobal", "Steamer", "Eliotrope", "Huppermage", "Ouginak", "Forgelance"
]

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_on_cooldown(user_id, data, cooldown_minutes=5):
    if user_id not in data:
        return False, None
    last_time_str = data[user_id].get("last_used")
    if not last_time_str:
        return False, None
    last_time = datetime.fromisoformat(last_time_str)
    now = datetime.utcnow()
    if now < last_time + timedelta(minutes=cooldown_minutes):
        return True, (last_time + timedelta(minutes=cooldown_minutes)) - now
    return False, None

def team_to_str(team):
    return "\n".join(f"• {cls}" for cls in team)

def validate_classes(classes):
    invalid = [c for c in classes if c not in ALL_CLASSES]
    return invalid

def get_available_classes(exclude_list):
    return [c for c in ALL_CLASSES if c not in exclude_list]

async def ask_confirmation(interaction, content, options):
    """
    Propose un menu simple de confirmation (select menu) avec options (list of str).
    Retourne l’option choisie ou None si timeout.
    """
    class Confirmation(discord.ui.Select):
        def __init__(self):
            super().__init__(placeholder="Choisis une option...", min_values=1, max_values=1,
                             options=[discord.SelectOption(label=opt) for opt in options])
            self.value = None

        async def callback(self, interaction2: discord.Interaction):
            self.value = self.values[0]
            self.view.stop()

    class View(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.select = Confirmation()
            self.add_item(self.select)

    view = View()
    await interaction.response.send_message(content, view=view, ephemeral=True)
    try:
        await view.wait(timeout=30)
    except asyncio.TimeoutError:
        return None
    return view.select.value

async def ask_reroll_or_new(bot, interaction):
    choice = await ask_confirmation(
        interaction,
        "Tu as déjà une team enregistrée.\nVeux-tu :",
        ["Refaire une nouvelle team complète", "Reroll un ou plusieurs personnages"]
    )
    return choice
def remove_team_classes(team, exclude_list):
    # Retire de la team toutes les classes qui sont dans exclude_list
    return [c for c in team if c not in exclude_list]

def remove_from_list(source, to_remove):
    # Retire les éléments de to_remove de la liste source
    return [x for x in source if x not in to_remove]

def get_reroll_pool(team, previous_team):
    # Retourne les classes disponibles pour reroll (hors celles de la team actuelle)
    return [c for c in ALL_CLASSES if c not in team]

def get_new_team_pool(previous_team):
    # Retourne les classes disponibles pour une nouvelle team (hors celles de l’ancienne)
    return [c for c in ALL_CLASSES if c not in previous_team]

def clean_class_name(name):
    return name.capitalize().strip()

def is_valid_class(name):
    return name in ALL_CLASSES

def parse_int(val):
    try:
        return int(val)
    except:
        return None

def format_team(team):
    return "\n".join(f"• {c}" for c in team)

def get_current_team(data, user_id):
    return data.get(user_id, {}).get("current_team", [])

def get_last_used(data, user_id):
    return data.get(user_id, {}).get("last_used", None)

def is_cooldown_active(data, user_id, cooldown=5):
    if user_id not in data:
        return False
    last_used_str = data[user_id].get("last_used", None)
    if not last_used_str:
        return False
    last_used = datetime.fromisoformat(last_used_str)
    return datetime.utcnow() < last_used + timedelta(minutes=cooldown)

def remaining_cooldown(data, user_id, cooldown=5):
    last_used_str = data[user_id].get("last_used", None)
    if not last_used_str:
        return timedelta(seconds=0)
    last_used = datetime.fromisoformat(last_used_str)
    remaining = (last_used + timedelta(minutes=cooldown)) - datetime.utcnow()
    return remaining if remaining.total_seconds() > 0 else timedelta(seconds=0)

def is_team_empty(team):
    return not team or len(team) == 0

def can_use_roulette(data, user_id):
    # Vérifie si le cooldown n’est pas actif
    return not is_cooldown_active(data, user_id)

def format_cooldown_string(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def has_team(data, user_id):
    return user_id in data and "current_team" in data[user_id] and bool(data[user_id]["current_team"])

def setup(bot: commands.Bot):
    @bot.tree.command(name="roulette", description="Tire une team aléatoire de classes Dofus.")
    @app_commands.describe(nombre="Nombre de personnages à tirer (1 à 8)")
    async def roulette(interaction: discord.Interaction, nombre: int):
        user_id = str(interaction.user.id)
        data = load_data()

        # Assure que la structure utilisateur existe
        if user_id not in data:
            data[user_id] = {
                "current_team": [],
                "previous_team": [],
                "last_used": "1970-01-01T00:00:00",
                "history": []
            }

        if not (1 <= nombre <= 8):
            await interaction.response.send_message("❌ Le nombre doit être entre 1 et 8.", ephemeral=True)
            return

        # Vérification du cooldown
        on_cd, remaining = is_on_cooldown(user_id, data)
        if on_cd:
            await interaction.response.send_message(
                f"⏳ Tu dois attendre encore {format_cooldown_string(remaining)} avant de relancer la roulette.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Si une team existe déjà, proposer choix reroll ou nouvelle team
        if has_team(data, user_id):
            choix = await ask_reroll_or_new(bot, interaction)
            if choix is None:
                await interaction.followup.send("⏳ Temps écoulé, commande annulée.", ephemeral=True)
                return

            if choix == "Refaire une nouvelle team complète":
                await interaction.followup.send("Combien de personnages veux-tu dans ta nouvelle team ? (1 à 8)", ephemeral=True)
                nombre_nouvelle_team = await ask_number(interaction, "Donne un nombre entre 1 et 8 :", 1, 8)
                if nombre_nouvelle_team is None:
                    return

                previous_team = get_current_team(data, user_id)
                pool = get_new_team_pool(previous_team)
                if nombre_nouvelle_team > len(pool):
                    await interaction.followup.send(f"❌ Impossible de tirer {nombre_nouvelle_team} classes, seulement {len(pool)} disponibles.", ephemeral=True)
                    return

                team = random.sample(pool, nombre_nouvelle_team)

                embed = discord.Embed(title="🎲 Roulette en cours...", color=discord.Color.orange())
                embed.set_image(url="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExdngwZWtzYzlyOG95YXFuNHNkbmxxYnFoZWd6bW5sODhtbGJtaDBybSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26uf2YTgF5upXUTm0/giphy.gif")
                message = await interaction.followup.send(embed=embed)

                current_display = []
                for cls in team:
                    await asyncio.sleep(3)
                    current_display.append(cls)
                    embed.description = team_to_str(current_display)
                    await message.edit(embed=embed)

                embed.title = "🎲 Team complète !"
                embed.set_image(url="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzgxYmNranhqb2xsNXZhdWVkdXl1dWV1OHJkNTkxb2hqMjB5a2RoMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9Igw8lZVGkO0hFle/giphy.gif")
                await message.edit(embed=embed)

                reset_cooldown(data, user_id)
                save_team(data, user_id, team)
                save_data(data)

                return

            elif choix == "Reroll un ou plusieurs personnages":
                team = get_current_team(data, user_id)
                if is_team_empty(team):
                    await interaction.followup.send("❌ Tu n'as pas de team à reroll.", ephemeral=True)
                    return

                team = await reroll_characters(bot, interaction, team)

                reset_cooldown(data, user_id)
                save_team(data, user_id, team)
                save_data(data)

                return

        # Sinon pas de team actuelle, tirage normal
        previous_team = get_current_team(data, user_id)
        available = get_available_classes(previous_team)
        if nombre > len(available):
            await interaction.followup.send(f"❌ Impossible de tirer {nombre} classes, seulement {len(available)} disponibles.", ephemeral=True)
            return

        team = random.sample(available, nombre)

        embed = discord.Embed(title="🎲 Roulette en cours...", color=discord.Color.orange())
        embed.set_image(url="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExdngwZWtzYzlyOG95YXFuNHNkbmxxYnFoZWd6bW5sODhtbGJtaDBybSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26uf2YTgF5upXUTm0/giphy.gif")
        message = await interaction.followup.send(embed=embed)

        current_display = []
        for cls in team:
            await asyncio.sleep(3)
            current_display.append(cls)
            embed.description = team_to_str(current_display)
            await message.edit(embed=embed)

        embed.title = "🎲 Team complète !"
        embed.description = team_to_str(team)  # Affiche la liste des classes dans l’embed
        embed.set_image(url="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzgxYmNranhqb2xsNXZhdWVkdXl1dWV1OHJkNTkxb2hqMjB5a2RoMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9Igw8lZVGkO0hFle/giphy.gif")
        await message.edit(embed=embed)
        
        reset_cooldown(data, user_id)
        save_team(data, user_id, team)
        save_data(data)
