import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')


class Leaderboard(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Leaderboard.py is ready!')

    @commands.command()
    async def leaderboard(self, ctx):

        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            database='nykzin_bot'
        )

        mycursor = mydb.cursor()

        mycursor.execute('SELECT * FROM user ORDER BY wallet DESC LIMIT 3')

        myresult = mycursor.fetchall()

        response_str = ''
        counter = 1

        for entry in myresult:
            disc_name = entry[2]
            wallet = entry[-1]

            response_str += f'**{counter}º** -> **{disc_name}** \
[G$ {wallet}]\n'
            counter += 1

        embed_message = discord.Embed(
                color=discord.Color.dark_blue()
            )
        embed_message.set_thumbnail(url=ctx.guild.icon)
        embed_message.add_field(
                name=f'LEADERBOARD DE __{ctx.guild.name.upper()}__',
                value=response_str
            )

        await ctx.send(embed=embed_message)


async def setup(client):
    await client.add_cog(Leaderboard(client))
