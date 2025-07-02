import discord
from discord import app_commands
from discord.ext import commands

def setup(bot: commands.Bot):
    @bot.tree.command(name="help", description="Affiche la liste des commandes disponibles.")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Commandes disponibles - DofuSpin",
            color=discord.Color.blue()
        )
        embed.add_field(name="/roulette", value="Tire une team aléatoire de classes Dofus (1 à 8).", inline=False)
        embed.add_field(name="/hardroulette", value="Tire une team aléatoire sans Feca, Pandawa, Enutrof, ni Cra.", inline=False)
        embed.add_field(name="/set", value="Définis ta team actuelle en listant les personnages.", inline=False)
        embed.add_field(name="/profile", value="Affiche ta team actuelle et cooldown.", inline=False)
        embed.add_field(name="/giveaway", value="Crée un giveaway (admins uniquement).", inline=False)
        embed.set_footer(text="DofuSpin Bot • Amuse-toi bien !")
        await interaction.response.send_message(embed=embed, ephemeral=True)
