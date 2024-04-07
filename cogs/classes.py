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
        params = {
            'api_key': RIOT_API_KEY
        }
        api_url = f'https://americas.api.riotgames.com/riot/account/v1/\
accounts/by-riot-id/{self.nickname}/{self.tag}'

        try:
            response = requests.get(api_url, params=urlencode(params))
            response.raise_for_status()
            summ_puuid = response.json()['puuid']
            return summ_puuid
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
