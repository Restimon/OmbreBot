import discord
import os
from discord.ext import commands
from config import TOKEN
import roulette  # roulette.py doit être dans le même dossier
import profile
import giveaway
import hardroulette

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    # Sync global : fonctionne sur tous les serveurs où le bot est invité
    await bot.tree.sync()
    print(f"✅ Connecté en tant que {bot.user} — commandes globales synchronisées.")

# Enregistre les commandes
roulette.setup(bot)
profile.setup(bot)
giveaway.setup(bot)
hardroulette.setup(bot)

# Démarre le bot
TOKEN = os.getenv("TOKEN")
