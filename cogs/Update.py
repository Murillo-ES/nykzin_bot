from .functions_and_classes import get_matches, update_db
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')


class Update(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Update.py is ready!')

    @commands.command(aliases=['att', 'atualiza'])
    async def update(self, ctx):

        await ctx.send('Atualizando o banco de dados, só um momento...')

        matches = get_matches()
        update_db(matches=matches)

        await ctx.send('Partidas atualizadas com sucesso!')


async def setup(client):
    await client.add_cog(Update(client))
