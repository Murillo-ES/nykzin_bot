from .functions_and_classes import get_match_info
import discord
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')


class Games(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Games.py is ready!')

    @commands.command()
    async def games(self, ctx):

        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            database='nykzin_bot'
        )

        mycursor = mydb.cursor()

        mycursor.execute('SELECT * FROM games WHERE winner = 0 ORDER BY date')

        myresult = mycursor.fetchall()

        response_str = ''

        today = datetime.now()

        for entry in myresult:
            date = entry[2]
            if date < today:
                continue

            game_id = entry[0]
            match_info = get_match_info(game_id=game_id)
            day = date.day
            month = date.month
            year = date.year
            time = date.time()

            response_str += f'{day}/{month}/{year} - {time}h -> {match_info} \
[Game ID: {game_id}]\nPara apostar: **!bet {game_id} Nome_do_Time Valor**\n\n'

        embed_message = discord.Embed(
                color=discord.Color.dark_blue()
            )
        embed_message.add_field(
            name='JOGOS DISPONÍVEIS P/ BETS',
            value=response_str
            )

        await ctx.send(embed=embed_message)


async def setup(client):
    await client.add_cog(Games(client))
