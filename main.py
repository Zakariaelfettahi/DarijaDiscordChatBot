import os
import discord

token = os.getenv('DISCORD_BOT_TOKEN')

class Client(discord.Client):
    async def on_ready(self):
        print(f"{self.user} connected successfully")
    
    async def on_message(self, message):
        if message.author == self.user:
            return  # Prevents an infinite loop of bot replying to itself

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(token)
