from database import get_matches, update_db
import discord
from discord.ext import commands, tasks
from itertools import cycle
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

BOT_STATUS = cycle(
    [
        '!mastery Nickname#TAG para buscar as 5 maiores maestrias do \
player.',
        '#TLWIN',
        '!match Nickname#TAG para verificar informações de partida em \
andamento.',
        '#GOPAIN',
        'Não tilte com os seus amiguinhos!'
    ]
)

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=discord.Intents.all())


not_cogs = ['classes.py', 'functions.py']


async def load():
    for filename in os.listdir('./cogs'):
        if (filename.endswith(".py")) and (filename not in not_cogs):
            await client.load_extension(f"cogs.{filename[:-3]}")


@tasks.loop(seconds=10)
async def change_status():
    await client.change_presence(activity=discord.Game(next(BOT_STATUS)))


@client.event
async def on_ready():
    print('Bot has connected to Discord succesfully')
    change_status.start()


async def main():
    async with client:
        await load()
        await client.start(DISCORD_TOKEN)

matches = get_matches()
update_db(matches=matches)

asyncio.run(main())
