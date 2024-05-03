import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import mysql.connector
from fuzzywuzzy import fuzz

load_dotenv()

RIOT_API_KEY = os.getenv('RIOT_API_KEY')
DB_PASSWORD = os.getenv('DB_PASSWORD')

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

# FUNCTIONS


def get_match_info(game_id: int):

    mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            database='nykzin_bot'
        )

    mycursor = mydb.cursor()

    sql = 'SELECT * FROM games WHERE game_id = %s'
    val = (game_id,)

    mycursor.execute(sql, val)

    myresult = mycursor.fetchone()

    team_1 = myresult[4]
    team_1_odd = myresult[5]
    team_2 = myresult[6]
    team_2_odd = myresult[7]

    return f'**{team_1}** (__{team_1_odd}__) vs **{team_2}** \
(__{team_2_odd}__)'


def update_bets(game_id: int, winner: int):

    mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password=DB_PASSWORD,
            database='nykzin_bot'
        )

    mycursor = mydb.cursor()

    sql = 'SELECT * FROM bets WHERE game_id = %s'
    val = (game_id,)

    mycursor.execute(sql, val)

    myresults = mycursor.fetchall()

    if len(myresults) == 0:
        print('No bets to be altered.')
    else:
        sql = f'SELECT team_{winner}_odd FROM games WHERE game_id = %s'
        val = (game_id,)

        mycursor.execute(sql, val)

        winner_odd = round(float(mycursor.fetchone()[0]), 2)

        for entry in myresults:
            bet_id = entry[0]
            user_id = entry[1]
            bet_side = int(entry[4])
            value = float(entry[3])

            sql = 'SELECT discord_id, discord_name, wallet FROM user WHERE \
user_id = %s'
            val = (user_id,)

            mycursor.execute(sql, val)
            myresult = mycursor.fetchone()

            disc_id = myresult[0]
            disc_name = myresult[1]
            wallet = float(myresult[2])

            bettor = Bettor(
                disc_id=disc_id,
                disc_name=disc_name,
                wallet=float(wallet)
            )

            sql = 'UPDATE bets SET status = "CLOSED" WHERE bet_id = %s'
            val = (bet_id,)

            mycursor.execute(sql, val)

            if bet_side == winner:
                bettor.deposit(value=value * winner_odd)

                sql = f'UPDATE user SET wallet = {bettor.wallet} WHERE \
user_id = %s'
                val = (user_id,)

                mycursor.execute(sql, val)

                mydb.commit()

                print(mycursor.rowcount, 'record(s) altered.')

            mydb.commit()

            print(mycursor.rowcount, 'record(s) altered.')


def get_matches():
    url = "https://www.rivalry.com/esports/league-of-legends-betting"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    betline_div = soup.find_all(
        'div',
        class_='betline m-auto betline-wide mb-0'
    )

    matches = []

    for div in betline_div:
        handicap_bet = div.find(
            'div',
            class_='text-2xs leading-1 text-navy dark:text-[#CFCFD1]'
        )
        is_handicap = handicap_bet is None

        if is_handicap:
            break

        league = div.find(
            'div',
            class_='text-league-of-legends-shade dark:text-league-of-legends-tint text-[11px]'
        ).text.strip()

        team_names = div.find_all('div', class_='outcome-name')
        team_one = team_names[0].text.strip()
        team_two = team_names[1].text.strip()

        team_odds = div.find_all('div', class_='outcome-odds')
        team_one_odd = float(team_odds[0].text.strip())
        team_two_odd = float(team_odds[1].text.strip())

        date_div = div.find(
            'div',
            class_='text-navy dark:text-[#CFCFD1] leading-3 text-[11px]'
        )

        date_strong = date_div.find('strong').text.strip()
        pt_month, day = date_strong.split()
        month = month_dict.get(pt_month.lower())
        raw_date = f'{month} {day} {datetime.now().year}'
        date_object = datetime.strptime(raw_date, '%b %d %Y')
        date = date_object.strftime('%Y-%m-%d')

        time_br = date_div.br.next_sibling.strip()
        raw_time_str = time_br.split()[0]
        time_obj = datetime.strptime(raw_time_str, '%H:%M')
        new_time_obj = time_obj - timedelta(hours=3)
        time = new_time_obj.strftime('%H:%M:%S')

        date_time = f'{date} {time}'

        matches.append(
            [
                league,
                date_time,
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

    sql = 'SELECT team_1, team_2, winner FROM games WHERE game_id = %s'
    val = (game_id,)

    mycursor.execute(sql, val)
    myresult = mycursor.fetchone()
    team_1 = myresult[0]
    team_2 = myresult[1]
    winner = int(myresult[2])

    if winner == 0:

        url = "https://e-sportstats.com/lol/matches-results"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        results_div = soup.find('div', class_='tournaments__list')
        matches = results_div.find_all('div', class_='tournament__item')
        similarity_list = []
        similarity_list_inv = []

        for match in matches:
            imgs = match.find_all('img', class_='image cn')
            match_team_1 = imgs[0].get('title')
            match_team_2 = imgs[3].get('title')

            similarity_1 = fuzz.ratio(team_1.lower(), match_team_1.lower())
            similarity_2 = fuzz.ratio(team_2.lower(), match_team_2.lower())
            total_similarity = similarity_1 + similarity_2
            similarity_list.append(total_similarity)

            similarity_1_inv = fuzz.ratio(team_1.lower(), match_team_2.lower())
            similarity_2_inv = fuzz.ratio(team_2.lower(), match_team_1.lower())
            total_inv_similarity = similarity_1_inv + similarity_2_inv
            similarity_list_inv.append(total_inv_similarity)

        max_value_1 = max(similarity_list)
        max_value_2 = max(similarity_list_inv)

        if (max_value_1 > max_value_2) or (max_value_1 == max_value_2):
            index = similarity_list.index(max_value_1)
            score_text = matches[index].find(
                'span',
                class_='match__score-value'
            ).text.strip()
            team_1_score = int(score_text[0])
            team_2_score = int(score_text[2])

            if team_1_score > team_2_score:
                sql = 'UPDATE games SET winner = 1 WHERE game_id = %s'
                val = (game_id,)

                mycursor.execute(sql, val)

                mydb.commit()

                print(f'Game ID {game_id} atualizado -> Vencedor: {team_1}')

                update_bets(game_id=game_id, winner=1)

            else:
                sql = 'UPDATE games SET winner = 2 WHERE game_id = %s'
                val = (game_id,)

                mycursor.execute(sql, val)

                mydb.commit()

                print(f'Game ID {game_id} atualizado -> Vencedor: {team_2}')

                update_bets(game_id=game_id, winner=2)

        elif max_value_2 > max_value_1:
            index = similarity_list_inv.index(max_value_2)
            score_text = matches[index].find(
                'span',
                class_='match__score-value'
            ).text.strip()
            team_1_score = int(score_text[2])
            team_2_score = int(score_text[0])

            if team_1_score > team_2_score:
                sql = 'UPDATE games SET winner = 2 WHERE game_id = %s'
                val = (game_id,)

                mycursor.execute(sql, val)

                mydb.commit()

                print(f'Game ID {game_id} atualizado -> Vencedor: {team_1}')

                update_bets(game_id=game_id, winner=1)

            else:
                sql = 'UPDATE games SET winner = 2 WHERE game_id = %s'
                val = (game_id,)

                mycursor.execute(sql, val)

                mydb.commit()

                print(f'Game ID {game_id} atualizado -> Vencedor: {team_2}')

                update_bets(game_id=game_id, winner=2)


def check_odds(game_id: int):

    mydb = mysql.connector.connect(
        host='localhost',
        user='root',
        password=DB_PASSWORD,
        database='nykzin_bot'
    )

    mycursor = mydb.cursor()

    sql = 'SELECT * FROM games WHERE game_id = %s'
    val = (game_id,)

    mycursor.execute(sql, val)

    myresult = mycursor.fetchone()

    team_1 = myresult[4]
    team_1_odd = myresult[5]
    team_2 = myresult[6]
    team_2_odd = myresult[7]

    url = "https://www.rivalry.com/esports/league-of-legends-betting"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    betline_div = soup.find_all(
        'div',
        class_='betline m-auto betline-wide mb-0'
    )

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
                sql = f'UPDATE games SET team_1_odd = {div_team_1_odd} \
WHERE game_id = %s'
                val = (game_id,)

                mycursor.execute(sql, val)

                mydb.commit()

                print(mycursor.rowcount, 'record(s) altered.')

            if div_team_2_odd != team_2_odd:
                sql = f'UPDATE games SET team_2_odd = {div_team_2_odd} \
WHERE game_id = %s'
                val = (game_id,)

                mycursor.execute(sql, val)

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

    sql = 'SELECT * FROM games WHERE winner = %s'
    val = ("0",)

    mycursor.execute(sql, val)

    myresult = mycursor.fetchall()

    for entry in myresult:
        game_id = entry[0]
        game_date = entry[2]
        closing_time = game_date + timedelta(hours=3)
        now = datetime.now()

        if closing_time < now:
            check_winner(game_id=game_id)

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

        sql = 'SELECT * FROM games WHERE team_1 = %s AND team_2 = %s'
        val = (team_1, team_2)

        mycursor.execute(sql, val)

        myresult = mycursor.fetchall()

        if len(myresult) == 0:
            sql = 'INSERT INTO games (league, date, winner, team_1, \
team_1_odd, team_2, team_2_odd) VALUES (%s, %s, 0, %s, \
%s, %s, %s)'
            val = (league, date, team_1, team_1_odd, team_2, team_2_odd,)

            mycursor.execute(sql, val)

            mydb.commit()

            print(f'1 record inserted. ID: {mycursor.lastrowid}')

        check_matches()


# CLASSES


class Player:
    def __init__(self, nickname, tag):
        self.nickname = nickname
        self.tag = tag
        self.riot_id = f'{nickname}#{tag}'

    @property
    def puuid(self):
        params = {'api_key': RIOT_API_KEY}
        puuid_url = f'https://americas.api.riotgames.com/riot/account/v1/\
accounts/by-riot-id/{self.nickname}/{self.tag}'

        try:
            puuid_response = requests.get(puuid_url, params=urlencode(params))
            puuid_response.raise_for_status()
            summ_puuid = puuid_response.json()['puuid']
            return summ_puuid
        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            return None

    @property
    def summoner_id(self):
        params = {'api_key': RIOT_API_KEY}
        summ_id_url = f'https://br1.api.riotgames.com/lol/summoner/v4/\
summoners/by-puuid/{self.puuid}'

        try:
            summ_id_response = requests.get(
                summ_id_url,
                params=urlencode(params)
            )
            summ_id_response.raise_for_status()
            summ_id = summ_id_response.json()['id']
            return summ_id
        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            return None

    @property
    def solo_stats(self):
        params = {'api_key': RIOT_API_KEY}
        solo_stats_url = f'https://br1.api.riotgames.com/lol/league/v4/\
entries/by-summoner/{self.summoner_id}'

        try:
            solo_stats_response = requests.get(
                solo_stats_url,
                params=urlencode(params)
            )
            solo_stats_response.raise_for_status()
            solo_stats = solo_stats_response.json()
            response = ''

            if solo_stats == []:
                return 'Unranked'

            else:
                for item in range(len(solo_stats)):
                    if solo_stats[item]['queueType'] == 'RANKED_SOLO_5x5':
                        tier = solo_stats[item]['tier'].capitalize()
                        rank = solo_stats[item]['rank']
                        wins = solo_stats[item]['wins']
                        losses = solo_stats[item]['losses']
                        lp = solo_stats[item]['leaguePoints']
                        if (
                            (tier == 'Challenger') or
                            (tier == 'Master')
                        ):
                            response = f'{tier} - {lp} PdL - {wins}/{losses}'
                        else:
                            response = f'{tier} {rank} - {lp} PdL - \
{wins}/{losses}'
                    else:
                        continue

            if response == '':
                return 'Unranked'
            else:
                return response

        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            return None

    @property
    def flex_stats(self):
        params = {'api_key': RIOT_API_KEY}
        flex_stats_api = f'https://br1.api.riotgames.com/lol/league/v4/\
entries/by-summoner/{self.summoner_id}'

        try:
            flex_stats_response = requests.get(
                flex_stats_api,
                params=urlencode(params)
            )
            flex_stats_response.raise_for_status()
            flex_stats = flex_stats_response.json()
            response = ''

            if flex_stats == []:
                return 'Unranked'

            else:
                for item in range(len(flex_stats)):
                    if flex_stats[item]['queueType'] == 'RANKED_FLEX_SR':
                        tier = flex_stats[item]['tier'].capitalize()
                        rank = flex_stats[item]['rank']
                        wins = flex_stats[item]['wins']
                        losses = flex_stats[item]['losses']
                        lp = flex_stats[item]['leaguePoints']
                        if (
                            (tier == 'Challenger') or
                            (tier == 'Master')
                        ):
                            response = f'{tier} - {lp} PdL - {wins}/{losses}'
                        else:
                            response = f'{tier} {rank} - {lp} PdL - \
{wins}/{losses}'
                    else:
                        continue

            if response == '':
                return 'Unranked'
            else:
                return response

        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            return None

    def get_mastery(self, champion_id):
        params = {
            'api_key': RIOT_API_KEY
            }
        api_url = f'https://br1.api.riotgames.com/lol/champion-mastery/v4/\
champion-masteries/by-puuid/{self.puuid}/by-champion/{champion_id}'

        try:
            response = requests.get(api_url, params=urlencode(params))
            response.raise_for_status()
            return response.json()['championPoints']
        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            return 0


class Bettor:
    def __init__(self, disc_id, disc_name, wallet=None):
        self.disc_id = disc_id
        self.disc_name = disc_name
        self.__wallet = 1000.0 if wallet is None else wallet

    @property
    def wallet(self):
        return self.__wallet

    def has_money(self, value):
        if self.wallet >= value:
            return True
        return False

    def withdraw(self, value):
        if self.has_money(value=value):
            self.__wallet -= value
            return f'Transação completa! Gold atual: {self.wallet}.'
        else:
            return f'Você não tem tanto gold assim, caloteiro! Gold atual: \
{self.wallet}.'

    def deposit(self, value):
        self.__wallet += value
        return f'Transação completa! Gold atual: {self.wallet}.'
