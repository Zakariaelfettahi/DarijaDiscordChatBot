import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # Get the guild ID from environment variable

# Intents need to be true for events to work
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def load_extensions():
  await bot.load_extension("commands_cog")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await load_extensions() # wait for the extension to load before continuing


bot.run(TOKEN)