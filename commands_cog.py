import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import csv
import os
import requests
import google.generativeai as genai

# Path configurations
JOKES_CSV_PATH = './jokes/jokes.csv'
PROVERBS_TXT_PATH = './proverbs/proverbs.csv'
COIN_IMAGES_PATH = './images/coins/'
HEADS_IMAGE = os.path.join(COIN_IMAGES_PATH, 'face.png')
TAILS_IMAGE = os.path.join(COIN_IMAGES_PATH, 'pile.png')
MEMES_PATH = './memes/'
TRANSLATIONS_DB_PATH = 'translations.db'

# Greetings and slurs lists
GREETINGS = ['hello', 'hi', 'slm', 'salam', 'salam alaikom', 'samaykom', 'cc', 'slt', 'yo', 'hola', 'allo', 'alo']
SLURS = ['zabi', 'zebi', 'thawa', 'tqwd', 't9wd', 't7wa', 'zaml', 'li7wak', 'li hwak', 'li 7wak', 'zamlbok', 'mok',
         'sir', 'lay', 'lyn3el', 'lyn3l', 'tbonmok', 'tbon', 'qhba', '9hba', 'zeb', 'w9', 'khtek', 'zobi', '7choun', 'zab']
FES = ["fes" , "FES" ,"Fes"]


class BotCommands(commands.Cog):
    def __init__(self, bot, gemini_api_key, weather_api_key):
        self.bot = bot
        self.gemini_api_key = gemini_api_key
        self.weather_api_key = weather_api_key

        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
        else:
            self.model = None

        self.BASE_URL = "https://api.weatherapi.com/v1/current.json"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if any(message.content.lower().startswith(greeting) for greeting in GREETINGS):
            await message.channel.send(f"Samaykom {message.author.mention}")

        if any(slur in message.content.lower() for slur in SLURS):
            await message.channel.send(f"Matkheserch lhdra a w9 {message.author.mention}")

        if any(fes in message.content.lower() for fes in FES):
          await message.channel.send(f"Fes li 7akma l3alam {message.author.mention}")


    @app_commands.command(name='terjem', description='Translate Arabic to English')
    async def terjem(self, interaction: discord.Interaction, text: str):
        def translate_word(word):
            conn = sqlite3.connect(TRANSLATIONS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(translations)")
            columns = [row[1] for row in cursor.fetchall() if row[1].startswith("n")]
            where_clause = " OR ".join([f"{col}=?" for col in columns]) + " OR darija_ar=? OR eng=?"
            cursor.execute(f"SELECT eng FROM translations WHERE {where_clause}", (*[word] * len(columns), word, word))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None

        words = text.split()
        translated_words = []
        unknown_words = []

        for word in words:
            translation = translate_word(word.lower())
            if translation:
                translated_words.append(translation)
            else:
                unknown_words.append(word)

        if unknown_words:
            await interaction.response.send_message("mafhemtekch, chof kifach tkteb f channel #how-to-write")
        else:
            translated_sentence = " ".join(translated_words) if translated_words else text
            await interaction.response.send_message(f"{text} → {translated_sentence}")

    @app_commands.command(name='nokta', description='Return a joke')
    async def nokta(self, interaction: discord.Interaction):
        if not os.path.exists(JOKES_CSV_PATH):
            await interaction.response.send_message("Jokes file not found!")
            return

        with open(JOKES_CSV_PATH, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            jokes = [row[0] for row in reader]

        if jokes:
            random_joke = random.choice(jokes)
            await interaction.response.send_message(random_joke)
        else:
            await interaction.response.send_message("No jokes available.")

    @app_commands.command(name='pileouface', description='Flip a coin (heads or tails)')
    async def pileouface(self, interaction: discord.Interaction):
        result = random.choice(["face", "pile"])
        file_path = HEADS_IMAGE if result == "face" else TAILS_IMAGE

        if not os.path.exists(file_path):
            await interaction.response.send_message("Coin image not found!")
            return

        file = discord.File(file_path, filename="coin.png")
        embed = discord.Embed(title="Coin Flip", description=f"Jatek **{result}**!", color=0xFFD700)
        embed.set_image(url="attachment://coin.png")
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name='maqoula', description='Return a proverb')
    async def maqoula(self, interaction: discord.Interaction):
        if not os.path.exists(PROVERBS_TXT_PATH):
            await interaction.response.send_message("Proverbs file not found!")
            return

        with open(PROVERBS_TXT_PATH, 'r', encoding='utf-8') as file:
            proverbs = file.readlines()

        if proverbs:
            random_proverb = random.choice(proverbs).strip()
            await interaction.response.send_message(random_proverb)
        else:
            await interaction.response.send_message("No proverbs available.")

    @app_commands.command(name='meme', description='Sends a random meme')
    async def meme(self, interaction: discord.Interaction):
        url = "https://meme-api.com/gimme"
        response = requests.get(url).json()

        if "url" in response:
            await interaction.response.send_message(response["url"])
        else:
            await interaction.response.send_message("Couldn't fetch a meme right now 😢")

    @app_commands.command(name="ai", description="Ask Gemini AI anything")
    async def ai(self, interaction: discord.Interaction, prompt: str):
        if not self.model:
            await interaction.response.send_message("Gemini AI is not available. Please check the API key.")
            return

        thinking_message = await interaction.response.send_message("⏳ Thinking...")

        try:
            response = self.model.generate_content(prompt)
            answer = response.text

            if len(answer) > 2000:
                answer = answer[:1997] + "..."

            await interaction.edit_original_response(content=f"**🤖 Gemini AI:**\n{answer}")

        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Error: {str(e)}")

    @app_commands.command(name='ljew', description='Get the current weather for a city.')
    async def ljew(self, interaction: discord.Interaction, city: str):
        url = f"{self.BASE_URL}?key={self.weather_api_key}&q={city}&aqi=no"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            temp_c = data['current']['temp_c']
            temp_f = data['current']['temp_f']
            condition = data['current']['condition']['text']
            wind_kph = data['current']['wind_kph']
            humidity = data['current']['humidity']
            feels_like = data['current']['feelslike_c']

            embed = discord.Embed(title=f"Ljew f {city.title()}", color = 0xADD8E6)
            embed.add_field(name="Ki dayra d3wa", value=condition, inline=False)
            embed.add_field(name="L7arara", value=f"{temp_c}°C / {temp_f}°F", inline=False)
            embed.add_field(name="L7arara bach ghat7es", value=f"{feels_like}°C", inline=False)
            embed.add_field(name="Sor3at riya7", value=f"{wind_kph} km/h", inline=False)
            embed.add_field(name="Rotouba", value=f"{humidity}%", inline=False)

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Sme7li, ma9derch nl9a ljew f **{city}**. 3afak 7awel mra okhra.")

    @app_commands.command(name='mo3awana', description='Displays all available commands and their descriptions.')
    async def mo3awana(self, interaction: discord.Interaction):
        desc_helpme = '__**Kifach tkhdem b lbot **__\n\n' \
        '**/nokta** = ila nghiti dhek 😂\n' \
        '**/maqoula** = ila bghiti l7ikma 🧐\n'\
        '**/terjem** = ila bghiti terjem mn darija l english (eg: !translate salam) 🇲🇦🇬🇧\n'\
        '**/pileouface** = ila tlefti w ma3refti madir, pile ou face 🎲\n'\
        '**/meme** = ila bghiti chi meme 🖼️\n'\
        '**/ai** = ila bghiti tswl l ai (gemini), text only 🤖\n'\
        '**/ljew** = ila bghiti t3ref ljew d chi mdina (eg: !ljew Csablanca) 🌦️\n'

        embed_var_helpme = discord.Embed(description=desc_helpme, color=0x00FF00)
        await interaction.response.send_message(embed=embed_var_helpme)


async def setup(bot):
    """
    This function is called by discord.py to load the cog.
    It's essential to have this for the cog to be recognized.
    """
    # Load API keys from environment variables.  This is safer than hardcoding them.
    gemini_api_key = os.getenv("GEMINI_API")
    weather_api_key = os.getenv("WEATHER_API")

    # Instantiate the cog with the bot instance and API keys.
    cog = BotCommands(bot, gemini_api_key, weather_api_key)

    # Add the cog to the bot.
    await bot.add_cog(cog)