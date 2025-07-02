import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
import random
from datetime import datetime, timedelta

def parse_duration(duration_str):
    regex = r"(\d+)([smhd])"
    match = re.match(regex, duration_str.lower())
    if not match:
        return None

    value, unit = match.groups()
    value = int(value)
    if unit == "s":
        return value
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    if unit == "d":
        return value * 86400
    return None

def format_time(seconds: int):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

def setup(bot: commands.Bot):
    @bot.tree.command(name="giveaway", description="Lancer un giveaway (admins uniquement).")
    @app_commands.describe(
        description="Ce que tu annonces / fêtes",
        reward="Ce que le gagnant remporte",
        winners="Nombre de gagnants (défaut: 1)",
        duration="Durée du giveaway (ex: 30s, 5m, 2h)"
    )
    async def giveaway(
        interaction: discord.Interaction,
        description: str,
        reward: str,
        winners: int = 1,
        duration: str = "1m"
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Tu dois être administrateur pour lancer un giveaway.", ephemeral=True)
            return

        total_seconds = parse_duration(duration)
        if total_seconds is None or total_seconds <= 0:
            await interaction.response.send_message("❌ Durée invalide. Utilise un format comme `30s`, `5m`, `1h`, `2d`.", ephemeral=True)
            return

        remaining_seconds = total_seconds
        embed = discord.Embed(
            title="🎉 Giveaway en cours !",
            description=f"{description}\n\n**Récompense :** {reward}",
            color=discord.Color.gold()
        )
        embed.add_field(name="🏆 Nombre de gagnants", value=str(winners))
        embed.add_field(name="⏳ Fin dans", value=format_time(remaining_seconds))
        embed.set_footer(text=f"Lancé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🎉")

        # Mise à jour toutes les 10 secondes
        update_interval = 10
        while remaining_seconds > 0:
            await asyncio.sleep(min(update_interval, remaining_seconds))
            remaining_seconds -= update_interval
            embed.set_field_at(1, name="⏳ Fin dans", value=format_time(max(remaining_seconds, 0)))
            await message.edit(embed=embed)

        # Fin du giveaway
        message = await interaction.channel.fetch_message(message.id)
        users = await message.reactions[0].users().flatten()
        users = [u for u in users if not u.bot]

        if not users:
            await interaction.followup.send("❌ Giveaway terminé, mais personne n'a participé.")
            return

        winners = min(winners, len(users))
        chosen = random.sample(users, winners)

        result = "🎊 **Giveaway terminé !** 🎊\n"
        result += f"**Récompense :** {reward}\n"
        result += "**Gagnant(s) :**\n" + "\n".join(f"• {u.mention}" for u in chosen)

        await interaction.followup.send(result)
