import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import csv
import os  # Import the 'os' module

class CommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot, GUILD_ID: str):
        self.bot = bot
        self.GUILD_ID = GUILD_ID
        if GUILD_ID:
            self.guild = discord.Object(id=int(GUILD_ID))  # Ensure GUILD_ID is an integer
        else:
            self.guild = None

    @app_commands.command(name="translate", description="Translate Arabic to English")
    async def translate(self, interaction: discord.Interaction, text: str):
        def translate_word(word):
            """Fetch translation by checking all 'nX' columns dynamically."""
            conn = sqlite3.connect("translations.db")
            cursor = conn.cursor()

            # Get all 'nX' columns from the table dynamically
            cursor.execute("PRAGMA table_info(translations)")
            columns = [row[1] for row in cursor.fetchall() if row[1].startswith("n")]

            # Dynamically build the WHERE clause for all possible 'nX' columns
            where_clause = " OR ".join([f"{col}=?" for col in columns]) + " OR darija_ar=? OR eng=?"
            cursor.execute(f"SELECT eng FROM translations WHERE {where_clause}", (*[word] * len(columns), word, word))

            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None  # if word found -> translation if not -> none

        words = text.split()
        translated_words = []
        unknown_words = []

        for word in words:
            translation = translate_word(word.lower())
            if translation:
                translated_words.append(translation)
            else:  # If word is not found
                unknown_words.append(word)  # Store the unknown word here

        if unknown_words:
            await interaction.response.send_message("mafhemtekch, chof kifach tkteb f channel #how-to-write")
        else:
            translated_sentence = " ".join(translated_words) if translated_words else text
            await interaction.response.send_message(f"{text} → {translated_sentence}")

    @app_commands.command(name="nokta", description="Return a joke")
    async def nokta(self, interaction: discord.Interaction):
      # Path of CSV files
      file_path_jokes = './jokes/jokes.csv'
      async def get_random_joke(file_path_jokes):
          with open(file_path_jokes, mode='r', newline='', encoding='utf-8') as file:
              reader = csv.reader(file)
              # Skip header
              next(reader)
              # Converts rows to a list of jokes
              jokes = [row[0] for row in reader]
              
          # Randomly selects a joke
          return random.choice(jokes)
      random_joke = await get_random_joke(file_path_jokes)
      # Sends the joke
      await interaction.response.send_message(random_joke)


    
    @app_commands.command(name="coinflip", description="Flip a coin (heads or tails)")
    async def coinflip(self, interaction: discord.Interaction):
        # Paths to coin images
        file_path_tails = "./images/coins/pile.png"
        file_path_head = "./images/coins/face.png"

        # Randomly choose heads or tails
        result = random.choice(["face", "pile"])
        file_path = file_path_head if result == "face" else file_path_tails

        # Check if the image file exists
        if not os.path.exists(file_path):
            await interaction.response.send_message("Coin image not found!")
            return

        # Open and send the image
        file = discord.File(file_path, filename="coin.png")
        embed = discord.Embed(title="Coin Flip", description=f"Jatek **{result}**!", color=0xFFD700)
        embed.set_image(url="attachment://coin.png")
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="maqoula", description="Return a proverb")
    async def coinflip(self, interaction: discord.Interaction):
        # Paths to coin images
        file_path_tails = "./images/coins/pile.png"
        file_path_head = "./images/coins/face.png"

        # Randomly choose heads or tails
        result = random.choice(["face", "pile"])
        file_path = file_path_head if result == "face" else file_path_tails

        # Check if the image file exists
        if not os.path.exists(file_path):
            await interaction.response.send_message("Coin image not found!")
            return

        # Open and send the image
        file = discord.File(file_path, filename="coin.png")
        embed = discord.Embed(title="Coin Flip", description=f"Jatek **{result}**!", color=0xFFD700)
        embed.set_image(url="attachment://coin.png")
        await interaction.response.send_message(embed=embed, file=file)

    @commands.Cog.listener()  # Decorator to indicate it's an event listener
    async def on_message(self, message):
        """Handles automatic greetings and slurs detection."""
        if message.author == self.bot.user:  # Use self.bot to access the bot instance
            return

        greetings = ['hello', 'hi', 'slm', 'salam', 'salam alaikom', 'samaykom', 'cc', 'slt', 'yo', 'hola', 'allo', 'alo']
        slurs = ['zabi', 'zebi', 'thawa', 'tqwd', 't9wd', 't7wa', 'zaml', 'li7wak', 'li hwak', 'li 7wak', 'zamlbok', 'mok', 
                 'sir', 'lay', 'lyn3el', 'lyn3l', 'tbonmok', 'tbon', 'qhba', '9hba', 'zeb', 'w9', 'khtek', 'zobi', '7choun', 'zab']

        if any(message.content.lower().startswith(greeting) for greeting in greetings):
            await message.channel.send(f"Samaykom {message.author}")

        if any(slur in message.content.lower() for slur in slurs):
            await message.channel.send(f"Matkheserch lhdra a w9 {message.author}")

        await self.bot.process_commands(message)  # Ensure commands still work, use self.bot

    @commands.Cog.listener()
    async def on_ready(self):
        if self.GUILD_ID:
            try:
                synced = await self.bot.tree.sync(guild=self.guild)
                print(f"Synced {len(synced)} command(s) for guild {self.GUILD_ID} from cog.")
            except Exception as e:
                print(f"Failed to sync commands for guild {self.GUILD_ID}: {e}")
        else:
            try:
                synced = await self.bot.tree.sync()
                print(f"Synced {len(synced)} command(s) globally from cog.")
            except Exception as e:
                print(f"Failed to sync global commands: {e}")

        commands = self.bot.tree.get_commands(guild=self.guild)
        if commands:
            print("Registered commands from cog:")
            for command in commands:
                print(f"- {command.name}: {command.description}")
        else:
            print("No commands are currently registered in the cog.")


async def setup(bot: commands.Bot):
    # Ensure GUILD_ID is loaded from the environment variables
    GUILD_ID = os.getenv("GUILD_ID")
    await bot.add_cog(CommandsCog(bot, GUILD_ID))