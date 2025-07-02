import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import json
import os
from datetime import datetime, timedelta

DATA_FILE = "roulette_data.json"
EXCLUDED_CLASSES = ["Feca", "Pandawa", "Enutrof", "Cra"]
ALL_CLASSES = [
    "Iop", "Cra", "Eniripsa", "Feca", "Sacrieur", "Xelor",
    "Ecaflip", "Sadida", "Osamodas", "Sram", "Pandawa", "Enutrof",
    "Roublard", "Zobal", "Steamer", "Eliotrope", "Huppermage", "Ouginak", "Forgelance"
]

VALID_CLASSES = [c for c in ALL_CLASSES if c not in EXCLUDED_CLASSES]

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
    @bot.tree.command(name="hardroulette", description="Tire une team aléatoire sans Feca, Pandawa, Enutrof ni Cra.")
    @app_commands.describe(nombre="Nombre de personnages à tirer (1 à 8)")
    async def hardroulette(interaction: discord.Interaction, nombre: int):
        if nombre < 1 or nombre > 8:
            await interaction.response.send_message("❌ Le nombre doit être entre 1 et 8.", ephemeral=True)
            return

        await interaction.response.defer()
        user_id = str(interaction.user.id)
        data = load_data()
        now = datetime.utcnow()

        if user_id in data:
            last_time = datetime.fromisoformat(data[user_id]["last_used"])
            if now < last_time + timedelta(minutes=5):
                remaining = (last_time + timedelta(minutes=5)) - now
                minutes = int(remaining.total_seconds() // 60)
                seconds = int(remaining.total_seconds() % 60)
                await interaction.followup.send(f"⏳ Tu dois attendre encore {minutes}m{seconds}s avant de relancer une roulette.")
                return

        previous_team = data.get(user_id, {}).get("current_team", [])
        available = [c for c in VALID_CLASSES if c not in previous_team]

        if nombre > len(available):
            await interaction.followup.send(
                f"❌ Impossible de tirer {nombre} classes. Il n'y a que {len(available)} classes valides disponibles.",
                ephemeral=True
            )
            return

        team = random.sample(available, nombre)

        embed = discord.Embed(title="🎲 HARD Roulette en cours...", color=discord.Color.red())
        message = await interaction.followup.send(embed=embed)

        current_display = []
        for cls in team:
            await asyncio.sleep(3)
            current_display.append(cls)
            embed.description = "\n".join(f"• {c}" for c in current_display)
            await message.edit(embed=embed)

        data[user_id] = {
            "current_team": team,
            "previous_team": previous_team,
            "last_used": now.isoformat(),
            "history": data.get(user_id, {}).get("history", []) + team
        }
        save_data(data)

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
                index = emojis.index(str(reaction.emoji))
                rerolled_class = team[index]
            
                reroll_pool = [c for c in VALID_CLASSES if c not in team]
                new_class = random.choice(reroll_pool)
                team[index] = new_class
            
                embed.title = "✅ Reroll effectué !"
                embed.description = "\n".join(f"• {c}" for c in team)
                await message.edit(embed=embed)
            
                data[user_id]["current_team"] = team
                data[user_id]["history"].append(new_class)
                save_data(data)
            
                # Enlever les réactions du bot et de l'utilisateur
                for emoji in emojis[:len(team)]:
                    await message.remove_reaction(emoji, bot.user)
                    await message.remove_reaction(emoji, interaction.user)
            
            except asyncio.TimeoutError:
                embed.title = "⏳ Temps écoulé ! Aucun reroll effectué."
                description = f"La team de {interaction.user.mention} est composée de :\n\n"
                description += "\n".join(f"• {c}" for c in team)
                description += "\n\nAinsi, la roulette a parlé !"
                embed.description = description
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                await message.edit(embed=embed)
            
                # Enlever les réactions du bot et de l'utilisateur aussi en cas de timeout
                for emoji in emojis[:len(team)]:
                    await message.remove_reaction(emoji, bot.user)
                    await message.remove_reaction(emoji, interaction.user)

