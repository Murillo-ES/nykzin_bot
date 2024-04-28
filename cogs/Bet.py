from .functions_and_classes import Bettor
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')


class Bet(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bet.py is ready!')

    @commands.command()
    async def bet(self, ctx, *, param):
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
            await ctx.send('Você não tá cadastrado, chefe. Usa "!registro" ou \
"!reg" primeiro ae.')

        param = param.split()
        game_id = param.pop(0)
        value = float(param.pop(-1))
        bet_name = ' '.join(param)
        user_id = myresult[0]
        disc_name = myresult[2]
        wallet = myresult[3]

        bettor = Bettor(disc_id=disc_id, disc_name=disc_name, wallet=wallet)

        today = datetime.now()

        mycursor.execute(f'SELECT * FROM games WHERE game_id = {game_id} AND \
winner = 0')
        myresult = mycursor.fetchone()

        if myresult is None:
            await ctx.send('Tem esse game não, loco. Usa "!games" ae e faz o \
negócio direito.')

        elif myresult[2] < today:
            await ctx.send('Não pode apostar nessa não, irmão. Usa "!games" \
ae, faz favor.')

        else:
            team_1 = myresult[4]
            team_2 = myresult[6]

            if (
                (bet_name != team_1) and
                (bet_name != team_2)
            ):
                await ctx.send('Mlk, vc é burro? Coloca o nome direito aí, \
vacilão (usa "!games" pra ver o nome do time.)')

            bet_side = 1 if team_1 == bet_name else 2

            try:
                if value <= wallet:

                    bettor.withdraw(value=value)

                    mycursor.execute(f'INSERT INTO bets (user_id, game_id, \
value, bet_side, status) VALUES ({user_id}, {game_id}, {value}, {bet_side}, \
"OPEN")')

                    mycursor.execute(f'UPDATE user SET wallet = \
{bettor.wallet} WHERE user_id = {user_id}')

                    mydb.commit()

                    await ctx.send(f'Você apostou G$ {value} em {bet_name}. \
Boa sorte!')

            except ValueError:

                await ctx.send('Pô, chefe, coloca um valor válido aí irmão, \
na moral.')


async def setup(client):
    await client.add_cog(Bet(client))
