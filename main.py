import discord

class Client(discord.Client):
    async def on_ready(self):
        print(f"{self.user} connected succsefully")
    
    async def on_message(self,message):
        print(f'message from {message.author}: {message.content}')

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run('MTM1MTAwODk1MTQ5MTIzMTg1Nw.G5SyK3.A7BaKgWz_145M7IKA312pgmrArAQXBNZJwdzZ4')