import discord
from discord import app_commands
from discord.ext import commands
import data  # ton module centralisé de gestion de données

ALL_CLASSES = [
    "Iop", "Cra", "Eniripsa", "Feca", "Sacrieur", "Xelor",
    "Ecaflip", "Sadida", "Osamodas", "Sram", "Pandawa", "Enutrof",
    "Roublard", "Zobal", "Steamer", "Eliotrope", "Huppermage", "Ouginak", "Forgelance"
]

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

        user_id = str(interaction.user.id)
        data_dict = data.load_data()
        data.ensure_user(data_dict, user_id)

        # Enregistrement avec data.py
        data.set_current_team(data_dict, user_id, classes)
        data.save_data(data_dict)

        # Confirmation embed
        embed = discord.Embed(
            title=f"✅ Team enregistrée pour {interaction.user.display_name}",
            description="\n".join(f"• {c}" for c in classes),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
