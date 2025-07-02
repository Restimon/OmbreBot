import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from collections import Counter

DATA_FILE = "roulette_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def reset_cooldown(data, user_id):
    if user_id not in data:
        data[user_id] = {}
    data[user_id]["last_used"] = datetime.utcnow().isoformat()

def setup(bot: commands.Bot):
    @bot.tree.command(name="profile", description="Affiche ta team actuelle et le temps avant ta prochaine roulette.")
    @app_commands.describe(user="Voir le profil d'un autre joueur (optionnel)")
    async def profile(interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        user_id = str(user.id)

        data = load_data()
        embed = discord.Embed(
            title=f"📜 Profil de {user.display_name}",
            color=discord.Color.blurple()
        )

        # Photo de profil
        embed.set_thumbnail(url=user.display_avatar.url)

        # Team actuelle
        team = data.get(user_id, {}).get("current_team", [])
        if team:
            embed.add_field(
                name="🎯 Team actuelle",
                value="\n".join(f"• {cls}" for cls in team),
                inline=False
            )
        else:
            embed.add_field(
                name="🎯 Team actuelle",
                value="Aucune team enregistrée.",
                inline=False
            )

        # Cooldown 5 minutes
        last_used_str = data.get(user_id, {}).get("last_used")
        if last_used_str:
            last_used = datetime.fromisoformat(last_used_str)
            now = datetime.utcnow()
            cooldown_end = last_used + timedelta(minutes=5)
            if now < cooldown_end:
                remaining = cooldown_end - now
                minutes = int(remaining.total_seconds() // 60)
                seconds = int(remaining.total_seconds() % 60)
                embed.add_field(
                    name="⏱️ Cooldown",
                    value=f"{minutes}m {seconds}s restants",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⏱️ Cooldown",
                    value="Disponible ✅",
                    inline=False
                )
        else:
            embed.add_field(
                name="⏱️ Cooldown",
                value="Jamais utilisé",
                inline=False
            )

        # Classe la plus tirée
        history = data.get(user_id, {}).get("history", [])
        if history:
            counts = Counter(history)
            top = counts.most_common(1)[0]  # (classe, nombre)
            embed.add_field(
                name="📈 Classe la plus tirée",
                value=f"{top[0]} ({top[1]} fois)",
                inline=False
            )

        await interaction.response.send_message(embed=embed)
