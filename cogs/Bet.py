from .functions_and_classes import Bettor
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv
import os
import mysql.connector
from fuzzywuzzy import fuzz

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')
FUZZ_THRESHOLD = 50


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

        sql = 'SELECT * FROM user WHERE discord_id = %s'
        val = (disc_id,)

        mycursor.execute(sql, val)

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

        sql = 'SELECT * FROM games WHERE game_id = %s AND winner = %s'
        val = (game_id, "0",)

        mycursor.execute(sql, val)

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

            similarity_1 = fuzz.ratio(bet_name.lower(), team_1.lower())
            similarity_2 = fuzz.ratio(bet_name.lower(), team_2.lower())

            if (
                (similarity_1) < FUZZ_THRESHOLD and
                (similarity_2) < FUZZ_THRESHOLD
            ):
                await ctx.send('Não sei de qual lado você tá fazendo essa \
bet, chefe =( verifica o nome do time e tenta de novo.)')
            elif similarity_1 > similarity_2:
                bet_side = 1
                bet_side_name = team_1
            elif similarity_2 > similarity_1:
                bet_side = 2
                bet_side_name = team_2
            else:
                await ctx.send('Não sei de qual lado você tá fazendo essa \
bet, chefe =( verifica o nome do time e tenta de novo.)')

#             if (
#                 (bet_name != team_1) and
#                 (bet_name != team_2)
#             ):
#                 await ctx.send('Mlk, vc é burro? Coloca o nome direito aí, \
# vacilão (usa "!games" pra ver o nome do time.)')

            try:
                if value <= wallet:

                    bettor.withdraw(value=value)

                    sql = 'INSERT INTO bets (user_id, game_id, value, \
bet_side, status) VALUES (%s, %s, %s, %s, %s)'
                    val = (user_id, game_id, value, bet_side, "OPEN",)

                    mycursor.execute(sql, val)

                    sql = 'UPDATE user SET wallet = %s WHERE user_id = %s'
                    val = (bettor.wallet, user_id,)

                    mycursor.execute(sql, val)

                    mydb.commit()

                    await ctx.send(f'Você apostou G$ {value} em \
{bet_side_name}. Boa sorte!')

            except ValueError:

                await ctx.send('Pô, chefe, coloca um valor válido aí irmão, \
na moral.')


async def setup(client):
    await client.add_cog(Bet(client))
