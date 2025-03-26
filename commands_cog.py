import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import csv
import os
import requests
import html
import asyncio
import google.generativeai as genai
import torch
import uuid
from diffusers import StableDiffusionPipeline

# Constants & Configurations
JOKES_CSV_PATH = './jokes/jokes.csv'
PROVERBS_TXT_PATH = './proverbs/proverbs.csv'
COIN_IMAGES_PATH = './images/coins/'
HEADS_IMAGE = os.path.join(COIN_IMAGES_PATH, 'face.png')
TAILS_IMAGE = os.path.join(COIN_IMAGES_PATH, 'pile.png')
MEMES_PATH = './memes/'
TRANSLATIONS_DB_PATH = 'translations.db'
OTDB_API_URL = "https://opentdb.com/api.php?amount=1&type=multiple"
WINNING_SCORE = 102400

# Greetings and Slurs (consider moving to config files)
GREETINGS = ['hello', 'hi', 'slm', 'salam', 'salam alaikom', 'samaykom', 'cc', 'slt', 'yo', 'hola', 'allo', 'alo']
SLURS = ['zabi', 'zebi', 'thawa', 'tqwd', 't9wd', 't7wa', 'zaml', 'li7wak', 'li hwak', 'li 7wak', 'zamlbok', 'mok',
         'sir', 'lay', 'lyn3el', 'lyn3l', 'tbonmok', 'tbon', 'qhba', '9hba', 'zeb', 'w9', 'khtek', 'zobi', '7choun', 'zab']
FES = ["fes", "FES", "Fes"]

# Global In-Memory Storage (will reset on bot restarts)
user_scores = {}

# Define the model ID for the stable diffusion version you want to use
model_id = "CompVis/stable-diffusion-v1-4"  # You can change this to "sd-legacy/stable-diffusion-v1-5" if needed

# Load the pipeline with the specified model
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)

# Move the pipeline to the MPS device (Mac M1 GPU)
pipe = pipe.to("mps")

class BotCommands(commands.Cog):
    """
    A Discord cog containing various commands and event listeners.
    """

    def __init__(self, bot, gemini_api_key, weather_api_key):
        """
        Initializes the BotCommands cog.

        Args:
            bot (discord.Client): The Discord bot instance.
            gemini_api_key (str): The API key for Gemini AI.
            weather_api_key (str): The API key for the Weather API.
        """
        self.bot = bot
        self.gemini_api_key = gemini_api_key
        self.weather_api_key = weather_api_key
        self.bot.persistent_views_added = False

        # Configure Gemini AI (if API key is provided)
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
        else:
            self.model = None

        self.weather_base_url = "https://api.weatherapi.com/v1/current.json"  # Consider making this a constant

    async def fetch_trivia_question(self):
        """Fetches a trivia question from the OpenTDB API."""
        try:
            response = requests.get(OTDB_API_URL)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if data['results']:
                return data['results'][0]  # Returns the first result
            else:
                print("No trivia questions found.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching trivia question: {e}")
            return None

    class TriviaView(discord.ui.View):  # Inheriting from discord.ui.View
        """
        A view containing interactive buttons for answering a trivia question.
        """

        def __init__(self, question_data, user_id):
            """
            Initializes the TriviaView.

            Args:
                question_data (dict): Data containing the trivia question and answers.
                user_id (int): The ID of the user who initiated the trivia game.
            """
            super().__init__(timeout=None)
            self.question_data = question_data  # Store the question data
            self.correct_answer = html.unescape(
                question_data['correct_answer'])  # Decode HTML entities in the correct answer
            incorrect_answers = [html.unescape(answer) for answer in
                                 question_data['incorrect_answers']]  # Decode HTML entities in incorrect answers
            self.answers = [self.correct_answer] + incorrect_answers
            random.shuffle(self.answers)
            self.user_id = user_id

            # Create buttons dynamically
            self.create_buttons()

        def create_buttons(self):
            """Creates and adds the answer buttons to the view."""
            button_labels = [answer[:80] for answer in self.answers]  # Truncate labels for Discord limit
            self.a_button = discord.ui.Button(style=discord.ButtonStyle.primary, label=button_labels[0],
                                               custom_id="button_a")
            self.b_button = discord.ui.Button(style=discord.ButtonStyle.primary, label=button_labels[1],
                                               custom_id="button_b")
            self.c_button = discord.ui.Button(style=discord.ButtonStyle.primary, label=button_labels[2],
                                               custom_id="button_c")
            self.d_button = discord.ui.Button(style=discord.ButtonStyle.primary, label=button_labels[3],
                                               custom_id="button_d")

            # Assign callbacks
            self.a_button.callback = self.create_callback(self.answers[0])
            self.b_button.callback = self.create_callback(self.answers[1])
            self.c_button.callback = self.create_callback(self.answers[2])
            self.d_button.callback = self.create_callback(self.answers[3])

            # Add buttons to the view
            self.add_item(self.a_button)
            self.add_item(self.b_button)
            self.add_item(self.c_button)
            self.add_item(self.d_button)

        def create_callback(self, button_answer):
            """Creates a callback function for a button."""

            async def callback(interaction: discord.Interaction):
                """Callback function executed when a button is pressed."""
                is_correct = (button_answer == self.correct_answer)  # Check if the answer is correct
                current_score = user_scores.get(self.user_id, 0)
                new_score = current_score * 2 if current_score > 0 else 100 # Double score or set initial to 100 if first time

                if is_correct:
                    user_scores[self.user_id] = new_score
                    if new_score >= WINNING_SCORE:
                        description = f"Congratulations! You've reached {WINNING_SCORE} and won the game!"
                    else:
                        description = f"Correct! You earned {new_score} points!"
                else:
                    description = f"Incorrect. The correct answer was {self.correct_answer}"
                    user_scores[self.user_id] = 0  # Reset score on wrong answer

                updated_score = user_scores.get(self.user_id, 0) # Get score AFTER update
                embed = discord.Embed(title="Trivia Result",
                                      description=f"{description}\nYour score: {updated_score}",
                                      color=discord.Color.green() if is_correct else discord.Color.red())

                if updated_score >= WINNING_SCORE:
                    del user_scores[self.user_id]
                    view = None # Game Over: remove view so they cannot play again
                else:
                    view = self

                await interaction.response.edit_message(embed=embed, view=view)

            return callback

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listens for messages and responds to greetings and slurs."""
        if message.author == self.bot.user:
            return

        content_lower = message.content.lower()  # Convert to lowercase once for efficiency

        if any(content_lower.startswith(greeting) for greeting in GREETINGS):
            await message.channel.send(f"Samaykom {message.author.mention}")

        if any(slur in content_lower for slur in SLURS):
            await message.channel.send(f"Matkheserch lhdra a w9 {message.author.mention}")

        if any(fes in content_lower for fes in FES):
            await message.channel.send(f"Fes li 7akma l3alam {message.author.mention}")

    @app_commands.command(name='terjem', description='Translate Arabic to English')
    async def terjem(self, interaction: discord.Interaction, text: str):
        """Translates a given Arabic text to English."""

        def translate_word(word):
            """Translates a single word using the SQLite database."""
            try:
                conn = sqlite3.connect(TRANSLATIONS_DB_PATH)
                cursor = conn.cursor()

                # Efficiently retrieve all 'n*' column names
                cursor.execute("PRAGMA table_info(translations)")
                columns = [row[1] for row in cursor.fetchall() if row[1].startswith("n")]

                # Construct WHERE clause dynamically
                where_clause = " OR ".join([f"{col}=?" for col in columns]) + " OR darija_ar=? OR eng=?"

                # Execute the query
                cursor.execute(f"SELECT eng FROM translations WHERE {where_clause}",
                               (*[word] * len(columns), word, word))
                result = cursor.fetchone()
                return result[0] if result else None # Return translation, if found
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                return None
            finally:
                if conn:
                    conn.close()

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
        """Returns a random joke from the jokes CSV file."""
        try:
            with open(JOKES_CSV_PATH, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
                jokes = [row[0] for row in reader]

            if jokes:
                random_joke = random.choice(jokes)
                await interaction.response.send_message(random_joke)
            else:
                await interaction.response.send_message("No jokes available.")

        except FileNotFoundError:
            await interaction.response.send_message("Jokes file not found!")
        except Exception as e:
            print(f"Error reading jokes: {e}")
            await interaction.response.send_message("An error occurred while retrieving a joke.")

    @app_commands.command(name='pileouface', description='Flip a coin (heads or tails)')
    async def pileouface(self, interaction: discord.Interaction):
        """Flips a coin and displays the result (heads or tails)."""
        result = random.choice(["face", "pile"])
        file_path = HEADS_IMAGE if result == "face" else TAILS_IMAGE

        try:
            file = discord.File(file_path, filename="coin.png")
            embed = discord.Embed(title="Coin Flip", description=f"Jatek **{result}**!", color=0xFFD700)
            embed.set_image(url="attachment://coin.png")
            await interaction.response.send_message(embed=embed, file=file)

        except FileNotFoundError:
            await interaction.response.send_message("Coin image not found!")
        except Exception as e:
            print(f"Error displaying coin flip: {e}")
            await interaction.response.send_message("An error occurred during the coin flip.")

    @app_commands.command(name='maqoula', description='Return a proverb')
    async def maqoula(self, interaction: discord.Interaction):
        """Returns a random proverb from the proverbs text file."""
        try:
            with open(PROVERBS_TXT_PATH, 'r', encoding='utf-8') as file:
                proverbs = [line.strip() for line in file] # Read all, strip each line

            if proverbs:
                random_proverb = random.choice(proverbs)
                await interaction.response.send_message(random_proverb)
            else:
                await interaction.response.send_message("No proverbs available.")

        except FileNotFoundError:
            await interaction.response.send_message("Proverbs file not found!")
        except Exception as e:
            print(f"Error reading proverbs: {e}")
            await interaction.response.send_message("An error occurred while retrieving a proverb.")

    @app_commands.command(name='meme', description='Sends a random meme')
    async def meme(self, interaction: discord.Interaction):
        """Sends a random meme from the meme-api."""
        try:
            url = "https://meme-api.com/gimme"
            response = requests.get(url).json()

            if "url" in response:
                await interaction.response.send_message(response["url"])
            else:
                await interaction.response.send_message("Couldn't fetch a meme right now 😢")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching meme: {e}")
            await interaction.response.send_message("Failed to retrieve a meme.  Please try again later.")

    @app_commands.command(name="ai", description="Ask Gemini AI anything")
    async def ai(self, interaction: discord.Interaction, prompt: str):
        """Asks Gemini AI a question and returns the answer."""
        if not self.model:
            await interaction.response.send_message("Gemini AI is not available. Please check the API key.")
            return

        await interaction.response.defer()  # Defer response to prevent timeout

        try:
            response = self.model.generate_content(prompt)
            answer = response.text

            if len(answer) > 2000:
                answer = answer[:1997] + "..."  # Truncate to Discord limit

            await interaction.followup.send(f"**🤖 Gemini AI:**\n{answer}") # Use followup for deferred responses

        except Exception as e:
            print(f"Gemini AI Error: {e}")  # Log the error
            await interaction.followup.send(f"❌ Error: {str(e)}")

    @app_commands.command(name="generate", description="Generate an AI image with stable diffusion")
    async def generate(self, interaction: discord.Interaction, prompt: str):
        """Generates an AI image based on the given prompt using Stable Diffusion."""
        await interaction.response.defer()  # Defer response to prevent timeout

        try:
            image = pipe(prompt).images[0]  # Generate the image

            # Save the image
            filename = f"{uuid.uuid4()}.png"
            image_path = os.path.join("generated_images", filename)
            os.makedirs("generated_images", exist_ok=True)  # Create directory if it doesn't exist
            image.save(image_path)

            # Send the image to Discord
            file = discord.File(image_path, filename=filename)
            embed = discord.Embed(title="🖼️ AI Generated Image", description=f"Prompt: `{prompt}`", color=0x00FF00)
            embed.set_image(url=f"attachment://{filename}")
            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            print(f"Stable Diffusion Error: {e}") # Log the error
            await interaction.followup.send(f"❌ Error: {str(e)}")

    @app_commands.command(name='ljew', description='Get the current weather for a city.')
    async def ljew(self, interaction: discord.Interaction, city: str):
        """Gets the current weather for a specified city."""
        try:
            url = f"{self.weather_base_url}?key={self.weather_api_key}&q={city}&aqi=no"
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            temp_c = data['current']['temp_c']
            temp_f = data['current']['temp_f']
            condition = data['current']['condition']['text']
            wind_kph = data['current']['wind_kph']
            humidity = data['current']['humidity']
            feels_like = data['current']['feelslike_c']

            embed = discord.Embed(title=f"Ljew f {city.title()}", color=0xADD8E6)
            embed.add_field(name="Ki dayra d3wa", value=condition, inline=False)
            embed.add_field(name="L7arara", value=f"{temp_c}°C / {temp_f}°F", inline=False)
            embed.add_field(name="L7arara bach ghat7es", value=f"{feels_like}°C", inline=False)
            embed.add_field(name="Sor3at riya7", value=f"{wind_kph} km/h", inline=False)
            embed.add_field(name="Rotouba", value=f"{humidity}%", inline=False)

            await interaction.response.send_message(embed=embed)

        except requests.exceptions.RequestException as e:
            print(f"Weather API Error: {e}")  # Log the error
            await interaction.response.send_message(f"Sme7li, ma9derch nl9a ljew f **{city}**. 3afak 7awel mra okhra.")
        except KeyError as e:
            print(f"Weather API data error: {e}") # Log data error
            await interaction.response.send_message("Failed to retrieve weather data for that city.")


    @app_commands.command(name='mo3awana', description='Displays all available commands and their descriptions.')
    async def mo3awana(self, interaction: discord.Interaction):
        """Displays a help message with all available commands."""
        desc_helpme = '__**Kifach tkhdem b lbot **__\n\n' \
        '**/nokta** = ila nghiti dhek 😂\n' \
        '**/maqoula** = ila bghiti l7ikma 🧐\n' \
        '**/terjem** = ila bghiti terjem mn darija l english (eg: !translate salam) 🇲🇦🇬🇧\n' \
        '**/pileouface** = ila tlefti w ma3refti madir, pile ou face 🎲\n' \
        '**/meme** = ila bghiti chi meme 🖼️\n' \
        '**/trivia** = ila bghiti tl3eb lo3ba dyal culture generale 🤓\n'
        '**/ai** = ila bghiti tswl l ai (gemini), text only 🤖\n' \
        '**/generate** = ila bghiti tgenerati tswira b l ai 📸\n' \
        '**/ljew** = ila bghiti t3ref ljew d chi mdina (eg: !ljew Csablanca) 🌦️\n'
                        
        embed_var_helpme = discord.Embed(description=desc_helpme, color=0x00FF00)
        await interaction.response.send_message(embed=embed_var_helpme)

    @app_commands.command(name="trivia", description="Asks a trivia question.")
    async def trivia(self, interaction: discord.Interaction):
        """Starts a trivia game by asking a question."""
        user_id = interaction.user.id
        question_data = await self.fetch_trivia_question()

        if question_data:
            question = question_data['question']
            embed = discord.Embed(title="Trivia Question:", description=question,
                                  color=discord.Color.blue())
            trivia_view = self.TriviaView(question_data, user_id)
            await interaction.response.send_message(embed=embed, view=trivia_view)
        else:
            await interaction.response.send_message("Failed to retrieve a trivia question. Please try again later.",
                                                   ephemeral=True)  # Make it ephemeral so it's only visible to user


    @commands.Cog.listener()
    async def on_ready(self):
        """Event listener called when the bot is ready."""
        if not self.bot.persistent_views_added:
            # TriviaView is persistent, but we no longer need to add it here because it's initiated when /trivia is called.
            # This is because the question changes.  If you only had one question, you could add it here.
            #trivia_view = self.TriviaView(None, None)  # Create an instance of TriviaView, providing dummy data.
            #self.bot.add_view(trivia_view)
            self.bot.persistent_views_added = True


async def setup(bot):
    """
    Loads the BotCommands cog into the bot.

    Args:
        bot (discord.Client): The Discord bot instance.
    """
    gemini_api_key = os.getenv("GEMINI_API")
    weather_api_key = os.getenv("WEATHER_API")
    await bot.add_cog(BotCommands(bot, gemini_api_key, weather_api_key))