import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Initialize the bot with a command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


async def load_extensions():
    """Loads all extensions (cogs) from the cogs directory."""
    for filename in os.listdir("./"): # Look in the current directory
        if filename.endswith(".py") and filename.startswith("commands_cog"): # Adjust filename accordingly
            try:
                await bot.load_extension(f"{filename[:-3]}")  # Remove '.py'
                print(f"Loaded extension: {filename}")
            except Exception as e:
                print(f"Failed to load extension {filename}: {e}")


async def main():
    await load_extensions()  # Load the cogs
    await bot.start(TOKEN)   # Start the bot

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())