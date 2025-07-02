import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import json
import os
from datetime import datetime, timedelta

DATA_FILE = "roulette_data.json"
ALL_CLASSES = [
    "Iop", "Cra", "Eniripsa", "Feca", "Sacrieur", "Xelor",
    "Ecaflip", "Sadida", "Osamodas", "Sram", "Pandawa", "Enutrof",
    "Roublard", "Zobal", "Steamer", "Eliotrope", "Huppermage", "Ouginak", "Forgelance"
]
EXCLUDED_CLASSES = ["Feca", "Pandawa", "Enutrof", "Cra"]
VALID_CLASSES = [c for c in ALL_CLASSES if c not in EXCLUDED_CLASSES]

GIF_PROGRESS = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExdngwZWtzYzlyOG95YXFuNHNkbmxxYnFoZWd6bW5sODhtbGJtaDBybSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26uf2YTgF5upXUTm0/giphy.gif"
GIF_FINAL = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzgxYmNranhqb2xsNXZhdWVkdXl1dWV1OHJkNTkxb2hqMjB5a2RoMyZlcD12MV9uZXJhbF9naWZfYnlfaWQmY3Q9Zw/xT9Igw8lZVGkO0hFle/giphy.gif"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def format_timedelta(td: timedelta):
    total_seconds = int(td.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

def setup(bot: commands.Bot):
    @bot.tree.command(name="hardroulette", description="Tire une team aléatoire de classes Dofus sans Feca, Pandawa, Enutrof et Cra.")
    @app_commands.describe(nombre="Nombre de personnages à tirer (1 à 8)")
    async def hardroulette(interaction: discord.Interaction, nombre: int = 4):
        if nombre < 1 or nombre > 8:
            await interaction.response.send_message("❌ Le nombre doit être entre 1 et 8.", ephemeral=True)
            return

        await interaction.response.defer()
        user_id = str(interaction.user.id)
        data = load_data()
        now = datetime.utcnow()

        # Cooldown 1h
        if user_id in data:
            last_time = datetime.fromisoformat(data[user_id]["last_used"])
            if now < last_time + timedelta(hours=1):
                remaining = (last_time + timedelta(hours=1)) - now
                await interaction.followup.send(
                    f"⏳ Tu dois attendre encore {format_timedelta(remaining)} avant de relancer la hardroulette.",
                    ephemeral=True
                )
                return

        previous_team = data.get(user_id, {}).get("current_team", [])
        available = [c for c in VALID_CLASSES if c not in previous_team]
        if len(available) < nombre:
            await interaction.followup.send(
                f"❌ Impossible de tirer {nombre} classes, seulement {len(available)} disponibles.",
                ephemeral=True
            )
            return

        team = random.sample(available, nombre)

        embed = discord.Embed(title="🎲 Hardroulette en cours...", color=discord.Color.orange())
        embed.set_image(url=GIF_PROGRESS)
        message = await interaction.followup.send(embed=embed)

        current_display = []
        for cls in team:
            await asyncio.sleep(3)
            current_display.append(cls)
            embed.description = "\n".join(f"• {c}" for c in current_display)
            await message.edit(embed=embed)

        embed.title = "🎲 Team complète !"
        embed.description = "\n".join(f"• {c}" for c in team)
        embed.set_image(url=GIF_FINAL)
        await message.edit(embed=embed)

        # Enregistrement
        data[user_id] = {
            "current_team": team,
            "previous_team": previous_team,
            "last_used": now.isoformat()
        }
        save_data(data)

        # Reroll unique si possible
        if len(team) > 1:
            embed.title = "🎯 Tu peux reroll **1 seul** personnage. Choisis via les réactions ci-dessous (30s)"
            await message.edit(embed=embed)

            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
            for i in range(len(team)):
                await message.add_reaction(emojis[i])

            def check(reaction, user):
                return (
                    user == interaction.user and
                    reaction.message.id == message.id and
                    str(reaction.emoji) in emojis[:len(team)]
                )

            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
                index = emojis.index(str(reaction.em
