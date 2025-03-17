import os
import discord

# Load token from environment variable
token = os.getenv('DISCORD_BOT_TOKEN')

class Client(discord.Client):
    async def on_ready(self):
        print(f"{self.user} connected successfully")
    
    #on message events
    async def on_message(self, message):
        # Prevent bot from replying to itself
        if message.author == self.user:
            return
        
        # List of greetings 
        greetings = ['hello', 'hi', 'slm', 'salam', 'salam alaikom', 'samaykom', 'cc', 'slt', 'yo', 'hola', 'allo', 'alo']
        slurs =     ['zabi', 'zebi', 'thawa','tqwd', 't9wd', 't7wa', 'zaml', 'li7wak', 'li hwak', 'li 7wak', 'zamlbok','mok' 
        'sir', 'lay', 'lyn3el', 'lyn3l', 'tbonmok', 'tbon', 'qhba', '9hba', 'zeb', 'w9', 'khtek', 'zobi', '7choun', 'zab']
        
        # Check message includes a greeting
        if any(message.content.lower().startswith(greeting) for greeting in greetings):
            await message.channel.send(f"Samaykom {message.author}")
        #check if message includes a slur
        if any(slur in message.content.lower() for slur in slurs):
            await message.channel.send(f"Matkheserch lhdra a w9 {message.author}")
    
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "🐀":
                await reaction.message.channel.send(f"{user.name}  caught you bitch")
        elif reaction.emoji == "🤡":
                await reaction.message.channel.send(f"{user.name} caught you bitch")
        
    


# Set up intents for receiving messages
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

# Run the client
client = Client(intents=intents)
client.run(token)
