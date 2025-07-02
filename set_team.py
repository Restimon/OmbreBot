import discord
from discord import app_commands
from discord.ext import commands
import json
import os

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

def setup(bot: commands.Bot):
    @bot.tree.command(name="set", description="Définis ta team actuelle en listant les personnages (ex: Iop, Cra, Eniripsa)")
    @app_commands.describe(team="Liste des classes séparées par des virgules")
    async def set_team(interaction: discord.Interaction, team: str):
        classes = [c.strip().capitalize() for c in team.split(",")]
        
        # Validation
        invalid = [c for c in classes if c not in ALL_CLASSES]
        if invalid:
            await interaction.response.send_message(
                f"❌ Classes invalides : {', '.join(invalid)}. Vérifie l'orthographe et les majuscules.",
                ephemeral=True
            )
            return
        
        if not (1 <= len(classes) <= 8):
            await interaction.response.send_message(
                "❌ Tu dois choisir entre 1 et 8 classes.",
                ephemeral=True
            )
            return
        
        # Chargement données
        user_id = str(interaction.user.id)
        data = load_data()

        # Enregistrement
        previous_history = data.get(user_id, {}).get("history", [])
        data[user_id] = {
            "current_team": classes,
            "previous_team": data.get(user_id, {}).get("current_team", []),
            "last_used": data.get(user_id, {}).get("last_used"),  # on ne modifie pas le cooldown
            "history": previous_history + classes
        }
        save_data(data)

        # Embed confirmation
        embed = discord.Embed(
            title=f"✅ Team enregistrée pour {interaction.user.display_name}",
            description="\n".join(f"• {c}" for c in classes),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
