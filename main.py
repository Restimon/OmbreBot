import discord
from discord.ext import commands
from config import TOKEN
import roulette  # roulette.py doit être dans le même dossier
import profile
import giveaway

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Sync global : fonctionne sur tous les serveurs où le bot est invité
    await bot.tree.sync()
    print(f"✅ Connecté en tant que {bot.user} — commandes globales synchronisées.")

# Enregistre la commande /roulette
roulette.setup(bot)
profile.setup(bot)
giveaway.setup(bot)

# Démarre le bot
bot.run(TOKEN)
