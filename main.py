import os
import discord

# Load token from environment variable
token = os.getenv('DISCORD_BOT_TOKEN')

class Client(discord.Client):
    async def on_ready(self):
        print(f"{self.user} connected successfully")
    
    async def on_message(self, message):
        # Prevent bot from replying to itself
        if message.author == self.user:
            return
        
        # List of greetings 
        greetings = ['hello', 'hi', 'slm', 'salam', 'salam alaikom', 'samaykom', 'cc', 'slt', 'yo']
        
        # Check message includes a greeting
        if any(message.content.lower().startswith(greeting) for greeting in greetings):
            await message.channel.send(f"Samaykom {message.author}")

# Set up intents for receiving messages
intents = discord.Intents.default()
intents.message_content = True

# Run the client
client = Client(intents=intents)
client.run(token)
