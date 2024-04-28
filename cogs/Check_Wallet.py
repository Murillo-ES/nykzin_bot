import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')


class CheckWallet(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Check_Wallet.py is ready!')

    @commands.command(aliases=['carteira'])
    async def check_wallet(self, ctx):
        disc_id = ctx.author.id

        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            database='nykzin_bot'
        )

        mycursor = mydb.cursor()

        mycursor.execute(f'SELECT * FROM user WHERE discord_id = {disc_id}')

        myresult = mycursor.fetchone()

        if myresult is None:
            await ctx.send('Você ainda não tem uma carteira D: usa \
"!registro" ou "!reg" pra começar a apostar!')

        disc_name = myresult[2]
        wallet = myresult[-1]

        embed_message = discord.Embed(
                color=discord.Color.dark_blue()
            )
        embed_message.set_thumbnail(url=ctx.author.display_avatar)
        embed_message.add_field(
            name=f'CARTEIRA DE {disc_name.upper()}',
            value=f'**G$ {wallet}**\n**Bets em aberto:** --//--'
            )

        await ctx.send(embed=embed_message)


async def setup(client):
    await client.add_cog(CheckWallet(client))
