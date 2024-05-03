from cogs.functions_and_classes import get_matches, update_db
import discord
from discord.ext import commands, tasks
from itertools import cycle
import os
import asyncio
from dotenv import load_dotenv
from random import choice

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TEAM_WIN_LIST = ['#PNGWIN', '#LLLWIN', '#TLWIN']

BOT_STATUS = cycle(
    [
        '!bet [Game_ID] [Nome do Time] [Valor] -> Fazer uma aposta em um game \
disponível.',
        choice(TEAM_WIN_LIST),
        '!carteira -> Mostra quanto você tem na carteira.',
        choice(TEAM_WIN_LIST),
        '!games -> Mostra os jogos disponíveis para realizar uma bet.',
        choice(TEAM_WIN_LIST),
        '!mastery [Nickname#TAG] -> Busca as 5 maiores maestrias do \
player.',
        choice(TEAM_WIN_LIST),
        '!leaderboard -> Mostra a galera mais rica do server.',
        choice(TEAM_WIN_LIST),
        '!match [Nickname#TAG] -> Verifica informações de partida em \
andamento.',
        choice(TEAM_WIN_LIST),
        '!obs OU !bets -> Mostra as bets que a galera fez até o momento.',
        choice(TEAM_WIN_LIST),
        '!registro OU !reg -> Registra seu usuário como um apostador nato do \
server.',
        choice(TEAM_WIN_LIST),
        '!att OU !atualiza -> Atualiza as info das partidas e bets.',
        choice(TEAM_WIN_LIST),
    ]
)

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=discord.Intents.all())


not_cogs = ['functions_and_classes.py']


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
