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
    @bot.tree.command(name="roulette", description="Tire une team aléatoire de classes Dofus.")
    @app_commands.describe(nombre="Nombre de personnages à tirer (1 à 8)")
    async def roulette(interaction: discord.Interaction, nombre: int = 4):
        if nombre < 1 or nombre > 8:
            await interaction.response.send_message("❌ Le nombre doit être entre 1 et 8.", ephemeral=True)
            return

        await interaction.response.defer()
        user_id = str(interaction.user.id)
        data = load_data()
        now = datetime.utcnow()

        # Cooldown 1h ou 5min selon le cooldown_type stocké
        cooldown_type = data.get(user_id, {}).get("cooldown_type", "roulette")
        last_time_str = data.get(user_id, {}).get("last_used")
        if last_time_str:
            last_time = datetime.fromisoformat(last_time_str)
            if cooldown_type == "roulette":
                cooldown_duration = timedelta(hours=1)
            else:
                cooldown_duration = timedelta(minutes=5)
            if now < last_time + cooldown_duration:
                remaining = (last_time + cooldown_duration) - now
                await interaction.followup.send(
                    f"⏳ Tu dois attendre encore {format_timedelta(remaining)} avant de relancer la roulette.",
                    ephemeral=True
                )
                return

        previous_team = data.get(user_id, {}).get("current_team", [])
        available = [c for c in ALL_CLASSES if c not in previous_team]
        if len(available) < nombre:
            await interaction.followup.send(
                f"❌ Impossible de tirer {nombre} classes, seulement {len(available)} disponibles.",
                ephemeral=True
            )
            return

        team = random.sample(available, nombre)

        embed = discord.Embed(title="🎲 Roulette en cours...", color=discord.Color.orange())
        embed.set_image(url=GIF_PROGRESS)
        message = await interaction.followup.send(embed=embed)

        current_display = []
        for cls in team:
            await asyncio.sleep(3)
            current_display.append(cls)
            embed.description = "\n".join(f"• {c}" for c in current_display)
            await message.edit(embed=embed)

        # Mise à jour de l'embed avec le gif final
        embed.title = "🎲 Team complète !"
        embed.description = "\n".join(f"• {c}" for c in team)
        embed.set_image(url=GIF_FINAL)
        await message.edit(embed=embed)

        # Enregistrement cooldown type roulette 1h
        data[user_id] = {
            "current_team": team,
            "previous_team": previous_team,
            "last_used": now.isoformat(),
            "cooldown_type": "roulette"
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
                index = emojis.index(str(reaction.emoji))
                rerolled_class = team[index]

                reroll_pool = [c for c in ALL_CLASSES if c not in team]
                if rerolled_class in reroll_pool:
                    reroll_pool.remove(rerolled_class)

                if not reroll_pool:
                    await interaction.followup.send("❌ Pas assez de classes disponibles pour reroll.", ephemeral=True)
                    return

                new_class = random.choice(reroll_pool)
                team[index] = new_class

                embed.title = "✅ Reroll effectué !"
                embed.description = "\n".join(f"• {c}" for c in team)
                embed.set_image(url=GIF_FINAL)
                await message.edit(embed=embed)

                # Supprime les réactions après reroll
                try:
                    await message.clear_reactions()
                except:
                    pass

                # Enregistrement cooldown reroll 5 minutes
                data[user_id]["current_team"] = team
                data[user_id]["last_used"] = datetime.utcnow().isoformat()
                data[user_id]["cooldown_type"] = "reroll"
                save_data(data)

            except asyncio.TimeoutError:
                embed.title = "⏳ Temps écoulé ! Aucun reroll effectué."
                await message.edit(embed=embed)
                try:
                    await message.clear_reactions()
                except:
                    pass
