from .classes import Player, RIOT_API_KEY
import discord
from discord.ext import commands
import requests
from urllib.parse import urlencode


class MatchAnalysis(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Match_Analysis.py is ready!')

    @commands.command(aliases=['match'])
    async def match_analysis(self, ctx, *, summoner):
        tag_index = summoner.find('#')
        summoner_name = summoner[:tag_index]
        gametag = summoner[tag_index + 1:]
        target_player = Player(nickname=summoner_name, tag=gametag)

        params = {
            'api_key': RIOT_API_KEY
        }

        match_url = f'https://br1.api.riotgames.com/lol/spectator/v5/\
active-games/by-summoner/{target_player.puuid}'

        champions_json = 'https://ddragon.leagueoflegends.com/cdn/14.6.1/data/\
en_US/champion.json'

        queue_json = 'https://static.developer.riotgames.com/docs/lol/\
queues.json'

        try:
            api_response = requests.get(match_url, params=urlencode(params))
            api_response.raise_for_status()
            await ctx.send('Partida encontrada! Só um segundo, chefe.')

            players_dict = {}
            counter = 1
            for item in api_response.json()['participants']:
                tag_index = item['riotId'].find('#')
                summoner_name = item['riotId'][:tag_index]
                gametag = item['riotId'][tag_index + 1:]
                players_dict[f'player{counter}'] = [
                    Player(nickname=summoner_name, tag=gametag),
                    item['championId']
                ]
                counter += 1

            players = []
            for item in list(players_dict.values()):
                players.append(item[0])

            champions_id = []
            for item in list(players_dict.values()):
                champions_id.append(item[1])

            players_nicknames = []
            for player in players:
                players_nicknames.append(player.nickname)

            masteries = []
            for player, id in list(players_dict.values()):
                masteries.append(player.get_mastery(id))

            queue_response = requests.get(queue_json)
            queue_response.raise_for_status()

            for item in range(len(queue_response.json())):
                if (
                    queue_response.json()[item]['queueId'] ==
                    api_response.json()['gameQueueConfigId']
                ):
                    queue_type = queue_response.json()[item]['description']
                    break

            champions_response = requests.get(champions_json)
            champions_response.raise_for_status()
            champions = champions_response.json()['data']

            champions_list = []
            for id in champions_id:
                for name in list(champions.keys()):
                    if champions[name]['key'] == str(id):
                        champions_list.append(champions[name]['id'])
                        break

            blue_side = []
            red_side = []
            counter = 0
            while counter <= 9:
                if len(blue_side) < 5:
                    blue_side.append(
                        f'**{players_nicknames[counter]}**: \
{champions_list[counter]} ({masteries[counter]} PM)'
                    )
                    counter += 1
                else:
                    red_side.append(
                        f'**{players_nicknames[counter]}**: \
{champions_list[counter]} ({masteries[counter]} PM)'
                    )
                    counter += 1

            blue_side_str = '\n'.join(blue_side)
            red_side_str = '\n'.join(red_side)

            embed_general = discord.Embed(
                title=f'Partida de **__{target_player.nickname}__**',
                color=discord.Color.dark_blue()
            )
            embed_general.add_field(name='MODO DE JOGO', value=queue_type)
            embed_general.add_field(
                name='BLUE SIDE',
                value=blue_side_str,
                inline=False
            )
            embed_general.add_field(name='RED SIDE', value=red_side_str)

            await ctx.send(embed=embed_general)

        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            await ctx.send('Deu certo isso aí não, amigo :/')


async def setup(client):
    await client.add_cog(MatchAnalysis(client))
