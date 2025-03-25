import discord
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3
import random
import csv
import os
import requests
import google.generativeai as genai

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
MEMES_PATH = './memes/'
TRANSLATIONS_DB_PATH = 'translations.db'

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

GEMINI_API_KEY = os.getenv("GEMINI_API")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

WEATHER_API_KEY = os.getenv("WEATHER_API")
BASE_URL = "https://api.weatherapi.com/v1/current.json"


# Greetings and slurs lists
GREETINGS = ['hello', 'hi', 'slm', 'salam', 'salam alaikom', 'samaykom', 'cc', 'slt', 'yo', 'hola', 'allo', 'alo']
SLURS = ['zabi', 'zebi', 'thawa', 'tqwd', 't9wd', 't7wa', 'zaml', 'li7wak', 'li hwak', 'li 7wak', 'zamlbok', 'mok',
         'sir', 'lay', 'lyn3el', 'lyn3l', 'tbonmok', 'tbon', 'qhba', '9hba', 'zeb', 'w9', 'khtek', 'zobi', '7choun', 'zab']
FES = ["fes" , "FES" ,"Fes"]
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
    
    # fes detection
    if any(fes in message.content.lower() for fes in FES):
      await message.channel.send(f"Fes li 7akma l3alam {message.author.mention}")

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

@bot.command(name='meme', help='Sends a random meme')
async def meme(ctx):
    url = "https://meme-api.com/gimme"
    response = requests.get(url).json()
    
    if "url" in response:
        await ctx.send(response["url"])
    else:
        await ctx.send("Couldn't fetch a meme right now 😢")

@bot.command(name='troll', help='Displays a random Moroccan meme')
async def meme(ctx):
    # Check if the memes directory exists
    if not os.path.exists(MEMES_PATH):
        await ctx.send("Memes directory not found!")
        return

    # List all files in the memes directory
    memes = [f for f in os.listdir(MEMES_PATH) if os.path.isfile(os.path.join(MEMES_PATH, f))]

    # Check if there are any memes available
    if not memes:
        await ctx.send("No memes available.")
        return

    # Select a random meme
    random_meme = random.choice(memes)
    file_path = os.path.join(MEMES_PATH, random_meme)

    # Send the meme
    with open(file_path, 'rb') as file:
        picture = discord.File(file)
        await ctx.send(file=picture)

@bot.command(name="ai", help="Ask Gemini AI anything")
async def ai(ctx, *, prompt: str):
    # Send initial "thinking..." message
    thinking_message = await ctx.send("⏳ Thinking...")

    try:
        # Generate the response from Gemini AI
        response = model.generate_content(prompt)
        answer = response.text

        # If the answer is too long for Discord, truncate it
        if len(answer) > 2000:
            answer = answer[:1997] + "..."

        # Edit the thinking message to show the actual answer
        await thinking_message.edit(content=f"**🤖 Gemini AI:**\n{answer}")

    except Exception as e:
        # In case of error, edit the thinking message to show the error
        await thinking_message.edit(content=f"❌ Error: {str(e)}")


@bot.command(name='ljew', help='Get the current weather for a city.')
async def ljew(ctx, *, city: str):
    # Create the URL with the city name and API key
    url = f"{BASE_URL}?key={WEATHER_API_KEY}&q={city}&aqi=no"
    
    # Send the request to WeatherAPI
    response = requests.get(url)
    data = response.json()

    # Check if the request was successful
    if response.status_code == 200:
        # Extract necessary data from the response
        temp_c = data['current']['temp_c']
        temp_f = data['current']['temp_f']
        condition = data['current']['condition']['text']
        wind_kph = data['current']['wind_kph']
        humidity = data['current']['humidity']
        feels_like = data['current']['feelslike_c']

        # Send the weather info as an embed
        embed = discord.Embed(title=f"Ljew f {city.title()}", color = 0xADD8E6)
        embed.add_field(name="Ki dayra d3wa", value=condition, inline=False)
        embed.add_field(name="L7arara", value=f"{temp_c}°C / {temp_f}°F", inline=False)
        embed.add_field(name="L7arara bach ghat7es", value=f"{feels_like}°C", inline=False)
        embed.add_field(name="Sor3at riya7", value=f"{wind_kph} km/h", inline=False)
        embed.add_field(name="Rotouba", value=f"{humidity}%", inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send(f"Sme7li, ma9derch nl9a ljew f **{city}**. 3afak 7awel mra okhra.")

@bot.command(name='mo3awana', help='Displays all available commands and their descriptions.')
async def mo3awana(ctx):
    desc_helpme = '__**Kifach tkhdem b lbot **__\n\n' \
    '**!nokta** = ila nghiti dhek 😂\n' \
    '**!maqoula** = ila bghiti l7ikma 🧐\n'\
    '**!translate** = ila bghiti terjem mn darija l english (eg: !translate salam) 🇲🇦🇬🇧\n'\
    '**!coinflip** = ila tlefti w ma3refti madir, pile ou face 🎲\n'\
    '**!meme** = ila bghiti chi meme 🖼️\n'\
    '**!ai** = ila bghiti tswl l ai (gemini), text only 🤖\n'\
    '**!ljew** = ila bghiti t3ref ljew d chi mdina (eg: !ljew Csablanca) 🌦️\n'\
    
    embed_var_helpme = discord.Embed(description=desc_helpme, color=0x00FF00)
    await ctx.send(embed=embed_var_helpme)

# Run the bot with your token
bot.run(TOKEN)
