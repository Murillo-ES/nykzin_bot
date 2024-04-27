from .classes import Bettor
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')


def get_match_info(game_id: int):

    mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            database='nykzin_bot'
        )

    mycursor = mydb.cursor()

    mycursor.execute(f'SELECT * FROM games WHERE game_id = {game_id}')

    myresult = mycursor.fetchone()

    team_1 = myresult[4]
    team_1_odd = myresult[5]
    team_2 = myresult[6]
    team_2_odd = myresult[7]

    return f'**{team_1}** (__{team_1_odd}__) vs **{team_2}** (__{team_2_odd}__)'


def update_bets(game_id: int, winner: int):

    mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            database='nykzin_bot'
        )

    mycursor = mydb.cursor()

    mycursor.execute(f'SELECT * FROM bets WHERE game_id = {game_id}')

    myresults = mycursor.fetchall()

    if len(myresults) == 0:
        print('No records to be altered.')
    else:
        winner_odd = round(mycursor.execute(f'SELECT team_{winner}_odd FROM games WHERE game_id = {game_id}'), 2)

        for entry in myresults:
            bet_id = entry[0]
            user_id = entry[1]
            bet_side = entry[4]
            value = entry[3]

            disc_id, disc_name, wallet = mycursor.execute(f'SELECT discord_id, discord_name, wallet FROM user WHERE user_id = {user_id}')
            bettor = Bettor(disc_id=disc_id, disc_name=disc_name, wallet=wallet)

            if bet_side == winner:
                bettor.deposit(value=value * winner_odd)

            mycursor.execute(f'UPDATE bets SET status = "CLOSED" WHERE bet_id = {bet_id}')

            mydb.commit()

            print(mycursor.rowcount, 'record(s) altered.')
