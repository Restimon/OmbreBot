import discord
from discord.ext import commands
from config import TOKEN
import roulette
import profile
import giveaway
import hardroulette

intents = discord.Intents.default()  # Crée les intents par défaut (ne contient pas les intents privilégiés)
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Connecté en tant que {bot.user} — commandes globales synchronisées.")

roulette.setup(bot)
profile.setup(bot)
giveaway.setup(bot)
hardroulette.setup(bot)

bot.run(TOKEN)
