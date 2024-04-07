import discord
from discord.ext import commands
import requests
from urllib.parse import urlencode
import os

from dotenv import load_dotenv
load_dotenv()

RIOT_API_KEY = os.getenv('RIOT_API_KEY')


def get_puuid(summoner_name, gametag):
    params = {
            'api_key': RIOT_API_KEY
        }
    api_url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/\
by-riot-id/{summoner_name}/{gametag}'

    try:
        response = requests.get(api_url, params=urlencode(params))
        response.raise_for_status()
        summ_puuid = response.json()['puuid']
        return summ_puuid
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')
        return None


class GetSummonerMastery(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Get_Mastery.py is ready!')

    @commands.command(aliases=['mastery'])
    async def get_mastery_by_name(self, ctx, *, summoner):
        tag_index = summoner.find('#')
        summoner_name = summoner[:tag_index]
        gametag = summoner[tag_index + 1:]

        params = {
            'api_key': RIOT_API_KEY
        }

        player_id = get_puuid(summoner_name=summoner_name, gametag=gametag)

        mastery_url = f'https://br1.api.riotgames.com/lol/champion-mastery/v4/\
champion-masteries/by-puuid/{player_id}/top?count=5'

        champions_json = 'https://ddragon.leagueoflegends.com/cdn/14.6.1/data/\
en_US/champion.json'

        summoner_url = f'https://br1.api.riotgames.com/lol/summoner/v4/\
summoners/by-puuid/{player_id}'

        try:
            mastery_response = requests.get(
                mastery_url,
                params=urlencode(params)
            )
            mastery_response.raise_for_status()

            champions_response = requests.get(champions_json)
            champions_response.raise_for_status()
            data = champions_response.json()['data']

            summoner_response = requests.get(
                summoner_url,
                params=urlencode(params)
            )
            summoner_response.raise_for_status()
            summoner_icon = summoner_response.json()['profileIconId']
            icon_url = f'https://ddragon.leagueoflegends.com/cdn/14.6.1/img/\
profileicon/{summoner_icon}.png'

            mastery_dict = {}
            for item in range(len(mastery_response.json())):

                champion = mastery_response.json()[item]['championId']
                for name in list(data.keys()):
                    if data[name]['key'] == str(champion):
                        champion = f'**{data[name]["id"]}**'
                        break

                mastery_points = mastery_response.json()[item][
                    'championPoints'
                ]

                mastery_dict[champion] = mastery_points

            response_list = []
            for key, value in mastery_dict.items():
                response_list.append(f'{key}: {value}')
            response = '\n'.join(response_list)

            embed_message = discord.Embed(
                title='PONTOS DE MAESTRIA',
                color=discord.Color.dark_blue()
            )
            embed_message.set_thumbnail(url=icon_url)
            embed_message.add_field(
                name=f'Player: __{summoner_name}__',
                value=response
            )

            await ctx.send(embed=embed_message)

        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            await ctx.send('Ué. Rolou algum erro, chefe X_X')


async def setup(client):
    await client.add_cog(GetSummonerMastery(client))
