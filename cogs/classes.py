import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
import os

load_dotenv()

RIOT_API_KEY = os.getenv('RIOT_API_KEY')


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
    def __init__(self, disc_id, disc_name):
        self.disc_id = disc_id
        self.disc_name = disc_name
        self.__wallet = 100.0

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
            return f'Transação completa! Gold atual: {self.wallet}'
        else:
            return f'Você não tem tanto gold assim, caloteiro! Gold atual: \
{self.wallet}'

    def deposit(self, value):
        self.__wallet += value
        return f'Transação completa! Gold atual: {self.wallet}'
