from .functions_and_classes import get_match_info
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')


class OpenBets(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Open_Bets.py is ready!')

    @commands.command(aliases=['obs', 'bets'])
    async def open_bets(self, ctx):

        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            database='nykzin_bot'
        )

        mycursor = mydb.cursor()

        sql = 'SELECT * FROM bets WHERE status = %s'
        val = ('OPEN',)

        mycursor.execute(sql, val)

        myresult = mycursor.fetchall()

        response_str = ''

        for entry in myresult:

            game_id = entry[2]

            mycursor.execute(f'SELECT discord_name FROM user WHERE user_id = \
{entry[1]}')
            bettor = mycursor.fetchone()[0]

            match_info = get_match_info(game_id=game_id)

            value = entry[3]

            mycursor.execute(f'SELECT team_{entry[4]} FROM games WHERE \
game_id = {game_id}')
            bet_side = mycursor.fetchone()[0]

            response_str += f'**{bettor}** apostou **G$ {value}** em \
{bet_side} no jogo {match_info} (Game ID: **{game_id}**)\n\n'

        embed_message = discord.Embed(
                color=discord.Color.dark_blue()
            )
        embed_message.add_field(
            name='BETS EM ABERTO',
            value=response_str
            )

        await ctx.send(embed=embed_message)


async def setup(client):
    await client.add_cog(OpenBets(client))
