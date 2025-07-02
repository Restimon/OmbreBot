import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
import random

# Convertit des durées type "1h", "30m", "45s" en secondes
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
        # Vérifie si l'utilisateur est admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Tu dois être administrateur pour lancer un giveaway.", ephemeral=True)
            return

        seconds = parse_duration(duration)
        if seconds is None:
            await interaction.response.send_message("❌ Durée invalide. Utilise un format comme `30s`, `5m`, `1h`, `2d`.", ephemeral=True)
            return

        # Création de l'embed du giveaway
        embed = discord.Embed(
            title="🎉 Giveaway en cours !",
            description=f"{description}\n\n**Récompense :** {reward}",
            color=discord.Color.gold()
        )
        embed.add_field(name="🏆 Nombre de gagnants", value=str(winners))
        embed.add_field(name="⏳ Fin dans", value=duration)
        embed.set_footer(text=f"Lancé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🎉")

        await asyncio.sleep(seconds)

        # Mise à jour du message pour annoncer les gagnants
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
