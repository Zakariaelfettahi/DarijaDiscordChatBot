
import discord
import os
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import csv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = discord.Object(id=1351009686253600819)

# intents need to be true for events to work
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

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

# path of csv file
file_path_jokes = './jokes/jokes.csv'
file_path_proverbs = "./proverbs/proverbs.csv"

# Function to randomly select a joke
async def get_random_joke(file_path_jokes):
    with open(file_path_jokes, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        # Skip header
        next(reader)
        # converts rows to a list of jokes
        jokes = [row[0] for row in reader]
        
    # randomly selects a joke
    return random.choice(jokes)

async def get_random_proverb(file_path_proverbs):
    with open(file_path_proverbs, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        # Skip header
        next(reader)
        # converts rows to a list of jokes
        proverbs = [row[0] for row in reader]
        
    # randomly selects a joke
    return random.choice(proverbs)


@bot.tree.command(name="translate", description="arabic->english", guild=GUILD_ID)
async def translate(interaction: discord.Interaction, text: str):
    words = text.split()
    translated_words = []
    unknown_words = []

    for word in words:
        translation = translate_word(word.lower())
        if translation:
            translated_words.append(translation) 
        else: #if word is not found 
            unknown_words.append(word)  # store the unknown word here

    if unknown_words:
        await interaction.response.send_message(f"mafhemtekch, chof kifach tkteb f channel #how-to-write")
    else:
        translated_sentence = " ".join(translated_words) if translated_words else text
        await interaction.response.send_message(f"{text} → {translated_sentence}")

@bot.tree.command(name="nokta", description="return a joke", guild=GUILD_ID)
async def nokta(interaction: discord.Interaction):
    #gets random joke
    random_joke = await get_random_joke(file_path_jokes)

    #writes the joke
    await interaction.response.send_message(random_joke)

@bot.tree.command(name="maqoula", description="return a proverb", guild=GUILD_ID)
async def maqoula(interaction: discord.Interaction):
    #gets random proverb
    random_proverb = await get_random_proverb(file_path_proverbs)

    #writes the proverb
    await interaction.response.send_message(random_proverb)
    

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync(guild=GUILD_ID)
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    """Handles automatic greetings and slurs detection."""
    if message.author == bot.user:
        return

    greetings = ['hello', 'hi', 'slm', 'salam', 'salam alaikom', 'samaykom', 'cc', 'slt', 'yo', 'hola', 'allo', 'alo']
    slurs = ['zabi', 'zebi', 'thawa', 'tqwd', 't9wd', 't7wa', 'zaml', 'li7wak', 'li hwak', 'li 7wak', 'zamlbok', 'mok', 
             'sir', 'lay', 'lyn3el', 'lyn3l', 'tbonmok', 'tbon', 'qhba', '9hba', 'zeb', 'w9', 'khtek', 'zobi', '7choun', 'zab']

    if any(message.content.lower().startswith(greeting) for greeting in greetings):
        await message.channel.send(f"Samaykom {message.author}")

    if any(slur in message.content.lower() for slur in slurs):
        await message.channel.send(f"Matkheserch lhdra a w9 {message.author}")

    await bot.process_commands(message)  # Ensure commands still work

@bot.event
async def on_reaction_add(reaction, user):
    """Handles specific emoji reactions."""
    if reaction.emoji == "🐀":
        await reaction.message.channel.send(f"{user.name} caught you bitch")
    elif reaction.emoji == "🤡":
        await reaction.message.channel.send(f"{user.name} caught you bitch")

bot.run(TOKEN)
