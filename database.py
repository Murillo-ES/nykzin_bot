from cogs.functions import update_bets
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import os
import mysql.connector
from fuzzywuzzy import fuzz

load_dotenv()

DB_PASSWORD = os.getenv('DB_PASSWORD')
FUZZ_THRESHOLD = 50

month_dict = {
    'jan': 'Jan',
    'fev': 'Feb',
    'mar': 'Mar',
    'abr': 'Apr',
    'mai': 'May',
    'jun': 'Jun',
    'jul': 'Jul',
    'ago': 'Aug',
    'set': 'Sep',
    'out': 'Oct',
    'nov': 'Nov',
    'dez': 'Dec'
}


def get_matches():
    url = "https://www.rivalry.com/esports/league-of-legends-betting"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    betline_div = soup.find_all('div', class_='betline m-auto betline-wide \
mb-0')

    matches = []

    for div in betline_div:
        league = div.find('div', class_='text-league-of-legends-shade \
dark:text-league-of-legends-tint text-[11px]').text.strip()

        team_names = div.find_all('div', class_='outcome-name')
        team_one = team_names[0].text.strip()
        team_two = team_names[1].text.strip()

        team_odds = div.find_all('div', class_='outcome-odds')
        team_one_odd = float(team_odds[0].text.strip())
        team_two_odd = float(team_odds[1].text.strip())

        date_div = div.find('div', class_='text-navy dark:text-[#CFCFD1] \
leading-3 text-[11px]')
        date_strong = date_div.find('strong').text.strip()
        pt_month, day = date_strong.split()
        month = month_dict.get(pt_month.lower())
        raw_date = f'{month} {day} {datetime.now().year}'
        date_object = datetime.strptime(raw_date, '%b %d %Y')
        date = date_object.strftime('%Y-%m-%d')

        matches.append(
            [
                league,
                date,
                [team_one, team_one_odd],
                [team_two, team_two_odd]
            ]
        )

    return matches


def check_winner(game_id: int):

    mydb = mysql.connector.connect(
        host='localhost',
        user='root',
        password=DB_PASSWORD,
        database='nykzin_bot'
    )

    mycursor = mydb.cursor()

    mycursor.execute(f'SELECT team_1, team_2 FROM games WHERE game_id = {game_id}')

    myresult = mycursor.fetchall()

    for teams in myresult:
        team_1 = teams[0]
        team_2 = teams[1]

    url = "https://e-sportstats.com/lol/matches-results"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results_div = soup.find('div', class_='tournaments__list')
    matches = results_div.find_all('div', class_='tournament__item')

    for match in matches:
        imgs = match.find_all('img', class_='image cn')
        match_team_1 = imgs[0].get('title')
        match_team_2 = imgs[3].get('title')

        similarity_1 = fuzz.ratio(team_1.lower(), match_team_1.lower())
        if similarity_1 >= FUZZ_THRESHOLD:
            similarity_2 = fuzz.ratio(team_2.lower(), match_team_2.lower())
            if similarity_2 >= FUZZ_THRESHOLD:

                mycursor.execute(f'SELECT winner FROM games WHERE game_id = {game_id}')
                winner = mycursor.fetchone()

                if winner == 0:

                    score = match.find('span', class_='match__score-value').text.strip()
                    team_1_score = int(score[0])
                    team_2_score = int(score[2])

                    if team_1_score > team_2_score:
                        mycursor.execute(f'UPDATE games SET winner = {1} WHERE game_id = {game_id}')

                        mydb.commit()

                        update_bets(game_id=game_id, winner=1)
                    else:
                        mycursor.execute(f'UPDATE games SET winner = {2} WHERE game_id = {game_id}')

                        mydb.commit()

                        update_bets(game_id=game_id, winner=2)


def check_odds(game_id: int):

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

    url = "https://www.rivalry.com/esports/league-of-legends-betting"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    betline_div = soup.find_all('div', class_='betline m-auto betline-wide \
mb-0')

    for div in betline_div:
        team_names = div.find_all('div', class_='outcome-name')
        div_team_1 = team_names[0].text.strip()
        div_team_2 = team_names[1].text.strip()

        team_odds = div.find_all('div', class_='outcome-odds')
        div_team_1_odd = float(team_odds[0].text.strip())
        div_team_2_odd = float(team_odds[1].text.strip())

        if (
            (div_team_1 == team_1) and
            (div_team_2 == team_2)
        ):
            if div_team_1_odd != team_1_odd:
                mycursor.execute(f'UPDATE games SET team_1_odd = {div_team_1_odd} WHERE game_id = {game_id}')

                mydb.commit()

                print(mycursor.rowcount, 'record(s) altered.')

            if div_team_2_odd != team_2_odd:
                mycursor.execute(f'UPDATE games SET team_2_odd = {div_team_2_odd} WHERE game_id = {game_id}')

                mydb.commit()

                print(mycursor.rowcount, 'record(s) altered.')


def check_matches():

    mydb = mysql.connector.connect(
        host='localhost',
        user='root',
        password=DB_PASSWORD,
        database='nykzin_bot'
    )

    mycursor = mydb.cursor()

    mycursor.execute('SELECT * FROM games')

    myresult = mycursor.fetchall()

    for entry in myresult:
        game_id = entry[0]
        game_date = entry[2]
        today = datetime.now().date()

        if game_date < today:
            check_winner(game_id=game_id)

        else:
            check_odds(game_id=game_id)


def update_db(matches: list):

    mydb = mysql.connector.connect(
        host='localhost',
        user='root',
        password=DB_PASSWORD,
        database='nykzin_bot'
    )

    mycursor = mydb.cursor()

    for item in range(len(matches)):
        league = matches[item][0]
        date = matches[item][1]
        team_1, team_1_odd = matches[item][2]
        team_2, team_2_odd = matches[item][3]

        mycursor.execute(f'SELECT * FROM games WHERE team_1 = "{team_1}" AND \
team_2 = "{team_2}"')

        myresult = mycursor.fetchall()

        if len(myresult) == 0:
            mycursor.execute(f'INSERT INTO games (league, date, winner, \
team_1, team_1_odd, team_2, team_2_odd) VALUES ("{league}", "{date}", 0, \
"{team_1}", {team_1_odd}, "{team_2}", {team_2_odd})')

            mydb.commit()

            print(f'1 record inserted. ID: {mycursor.lastrowid}')

    check_matches()
