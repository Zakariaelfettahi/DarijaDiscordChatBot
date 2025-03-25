import discord
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3
import random
import csv
import os

# Initialize the bot with a command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Path configurations
JOKES_CSV_PATH = './jokes/jokes.csv'
PROVERBS_TXT_PATH = './proverbs/proverbs.csv'
COIN_IMAGES_PATH = './images/coins/'
HEADS_IMAGE = os.path.join(COIN_IMAGES_PATH, 'face.png')
TAILS_IMAGE = os.path.join(COIN_IMAGES_PATH, 'pile.png')
TRANSLATIONS_DB_PATH = 'translations.db'
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Greetings and slurs lists
GREETINGS = ['hello', 'hi', 'slm', 'salam', 'salam alaikom', 'samaykom', 'cc', 'slt', 'yo', 'hola', 'allo', 'alo']
SLURS = ['zabi', 'zebi', 'thawa', 'tqwd', 't9wd', 't7wa', 'zaml', 'li7wak', 'li hwak', 'li 7wak', 'zamlbok', 'mok',
         'sir', 'lay', 'lyn3el', 'lyn3l', 'tbonmok', 'tbon', 'qhba', '9hba', 'zeb', 'w9', 'khtek', 'zobi', '7choun', 'zab']

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Greeting response
    if any(message.content.lower().startswith(greeting) for greeting in GREETINGS):
        await message.channel.send(f"Samaykom {message.author.mention}")

    # Slur detection and warning
    if any(slur in message.content.lower() for slur in SLURS):
        await message.channel.send(f"Matkheserch lhdra a w9 {message.author.mention}")

    await bot.process_commands(message)

@bot.command(name='translate', help='Translate Arabic to English')
async def translate(ctx, *, text: str):
    def translate_word(word):
        """Fetch translation by checking all 'nX' columns dynamically."""
        conn = sqlite3.connect(TRANSLATIONS_DB_PATH)
        cursor = conn.cursor()

        # Get all 'nX' columns from the table dynamically
        cursor.execute("PRAGMA table_info(translations)")
        columns = [row[1] for row in cursor.fetchall() if row[1].startswith("n")]

        # Dynamically build the WHERE clause for all possible 'nX' columns
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
        await ctx.send("mafhemtekch, chof kifach tkteb f channel #how-to-write")
    else:
        translated_sentence = " ".join(translated_words) if translated_words else text
        await ctx.send(f"{text} → {translated_sentence}")

@bot.command(name='nokta', help='Return a joke')
async def nokta(ctx):
    if not os.path.exists(JOKES_CSV_PATH):
        await ctx.send("Jokes file not found!")
        return

    with open(JOKES_CSV_PATH, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        jokes = [row[0] for row in reader]

    if jokes:
        random_joke = random.choice(jokes)
        await ctx.send(random_joke)
    else:
        await ctx.send("No jokes available.")

@bot.command(name='coinflip', help='Flip a coin (heads or tails)')
async def coinflip(ctx):
    result = random.choice(["face", "pile"])
    file_path = HEADS_IMAGE if result == "face" else TAILS_IMAGE

    if not os.path.exists(file_path):
        await ctx.send("Coin image not found!")
        return

    file = discord.File(file_path, filename="coin.png")
    embed = discord.Embed(title="Coin Flip", description=f"Jatek **{result}**!", color=0xFFD700)
    embed.set_image(url="attachment://coin.png")
    await ctx.send(embed=embed, file=file)

@bot.command(name='maqoula', help='Return a proverb')
async def maqoula(ctx):
    if not os.path.exists(PROVERBS_TXT_PATH):
        await ctx.send("Proverbs file not found!")
        return

    with open(PROVERBS_TXT_PATH, 'r', encoding='utf-8') as file:
        proverbs = file.readlines()

    if proverbs:
        random_proverb = random.choice(proverbs).strip()
        await ctx.send(random_proverb)
    else:
        await ctx.send("No proverbs available.")

# Run the bot with your token
bot.run(TOKEN)
