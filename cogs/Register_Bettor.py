from discord.ext import commands
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')


class RegisterBettor(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Register_Bettor.py is ready!')

    @commands.command(aliases=['registro', 'reg'])
    async def register_bettor(self, ctx):
        discord_id = ctx.author.id
        discord_name = ctx.author.global_name

        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            database='nykzin_bot'
        )

        mycursor = mydb.cursor()

        mycursor.execute(f'SELECT * FROM user WHERE discord_id = {discord_id}')

        myresult = mycursor.fetchall()

        if len(myresult) == 0:
            sql = "INSERT INTO user (discord_id, discord_name, \
wallet) VALUES (%s, %s, %s)"
            val = (discord_id, discord_name, 1000.0,)

            mycursor.execute(sql, val)
            mydb.commit()

            print(f'1 record inserted. ID: {mycursor.lastrowid}')
            await ctx.send('Tá cadastrado, paizão!')
        else:
            await ctx.send('Você já tá cadastrado, mlk, osh.')


async def setup(client):
    await client.add_cog(RegisterBettor(client))
