import aiohttp
import asyncio
import re
import dill
from concurrent.futures import ThreadPoolExecutor

from itertools import repeat

import time
import requests
import win32api
from bs4 import BeautifulSoup
from fuzzywuzzy import process
from riotwatcher import LolWatcher, RiotWatcher, ApiError
from league import credential

watcher = LolWatcher(credential.get_key())
riot = RiotWatcher(credential.get_key())

class MMR():
    def __init__(self, mmr, err, name, id) -> None:
        self.mmr = mmr
        self.err = err
        self.name = name
        self.id = id

    def set_rank(self, rank):
        self.rank = rank

    def set_time(self, time):
        self.time = time


"""
    Get MMR for one Summoner usng whatismymmr

    @param name: Summoner name string
    @return: MMR int, MMR std int, name string
    @raise None: No aram value for this summoner
""" 
def get_mmr(name) -> MMR:
    name = name[0]
    id = name[1]
    r = requests.get('https://na.whatismymmr.com/api/v1/summoner?name=' + name)
    r = r.json()
    try:
        if r["ARAM"]["avg"]:
            return MMR(r["ARAM"]["avg"], r["ARAM"]["err"], name, id)
    except:
        print("NO VALUE FOR", name)


"""
    Get MMR for one Summoner usng whatismymmr

    @param name: Summoner name string
    @return: MMR int, MMR std int, name string
    @raise None: No aram value for this summoner
""" 
def get_high_mmr_players(args):
    id, mmrf, namesf = args

    mmr = mmrf.get(id)
    names = namesf.get(id)
    if mmr or names:
        return mmr, names
    

"""
    Get Aram Leaderboard from aram.moe

    @return: Dirty Doughnut: ("16", "3492 ± 0")
"""
def get_ranks(content):
    
    output = {}
    soup = BeautifulSoup(content, "html.parser")
    results = soup.find_all(class_="player-container")
    for i in results:
        p = re.compile(r'<div class="player-container"><span class="num">(.+)</span><span class="name">(.+)</span><span class="mmr">(.+)</span></div>')
        m = p.match(str(i))
        if m is not None:
            output[m.group(2)] = (m.group(1), m.group(3))
    return output



async def get(args):
    print("in")
    print(time.time())
    id, mmrf, namesf = args
    name = await conn.request('get', '/lol-summoner/v1/summoners/' + str(id))
    name = await name.json()
    puuid = riot.account.by_riot_id('americas', name['gameName'], name['tagLine'])['puuid']

    mmr = mmrf.get(puuid)
    names = namesf.get(puuid)
    print("out")
    print(time.time())
    if mmr or names:
        return mmr, names


def load_pickles(file_type):
    path = f"league/cache/ids_to_{file_type}.pickle"
    with open(path, "rb") as file:
        pickle = dill.load(file)
    return pickle

"""
    Display ARAM MMR using LCU Driver
    Fuzzy search for ranking due to aram.moe name consistency issues.
    Use whatismymmr mmr values, aram.moe only updates daily.

    @param champ_select: REST API response from champ_select call using LCU Driver
    @param conn: Connector of LCU Driver
    @return: None, Displays ex.     3 players: 2381 ± 42
                                014 Dirty Doughnut: 3480 ± 10
                                047 Fennriss: 3425 ± 11
                                XXX derroz: 1550 ± 92
""" 
async def display_mmr(champ_select, connection):
    global conn
    conn = connection

    timestamp = time.time()

    ids = [i["summonerId"] for i in champ_select["myTeam"] if i != 0]

    names = []
    result = [] 
    with ThreadPoolExecutor(max_workers=5) as pool:
        names = list(pool.map(get_name, ids))
        names = await asyncio.gather(*names)
        result = list(pool.map(get_mmr, names))


    result = [i for i in result if i]
    count = len(result)
    
    if count == 1:
        win32api.MessageBox(0, "Sht\nCnt\nBad\nPlayers", "BUNCH OF SHITTERS", 0x00001000) 
        return

    mmr = sum([i[0] for i in result]) / count
    err = sum([i[1] for i in result]) / count

    avg = f"{count} players: {round(mmr)} ±{round(err)}"

    ranks = []
    page_request = requests.get("https://aram.moe/")
    top500 = get_ranks(page_request.content)

    lowest500 = min([int(i[0]) for i in top500.values()])
    for res in result:
        mmr, err, name = res
        ranking = "XXX"
        if name in top500:
            rank_value = int(top500[name][0])
            ranking = f'{rank_value:03d}'
        else:
            fuzzy_name = process.extractOne(name, top500.keys(), score_cutoff=90)
            if mmr >= lowest500 and fuzzy_name in top500:
                print("fuzzy", fuzzy_name, mmr, ">", lowest500)
                rank_value = int(top500[fuzzy_name][0])
                ranking = f'~{rank_value:03d}'

        res.set_rank(rank_value)
        res.set_time(timestamp)
        ranks.append([ranking, name, mmr, err])
     
    output = ""
    for i in sorted(ranks, key=lambda x: x[2], reverse=True):
        output += f'#{i[0]} {i[1]}: {i[2]} ± {i[3]}\n'
    
    win32api.MessageBox(0, output, avg, 0x00001000) 

"""
    Display ARAM Historically High MMR Players using LCU Driver
    Using Precalculated high mmr players in moe/t.py

    @param champ_select: REST API response from champ_select call using LCU Driver
    @param conn: Connector of LCU Driver
    @return: None, Displays ex.     3 players: 3038 ± 0
                                    Dirty Doughnut: 3480
                                       Fennriss: 3425
                                       Fenix MG: 3XXX
""" 
async def display_high_mmr(champ_select, connection):
    global conn
    conn = connection
    mmrd, namesd = load_pickles("mmr"), load_pickles("names")

    result = [] 
    ids = [i["summonerId"] for i in champ_select["myTeam"] if i != 0]
    
    with ThreadPoolExecutor(max_workers=5) as pool:
        args = zip(ids, repeat(mmrd), repeat(namesd))
        result = await asyncio.gather(*list(pool.map(get, args)))


    result = [i for i in result if i]
    count = len(result)
    
    if count == 1:
        win32api.MessageBox(0, "Sht\nCnt\nBad\nPlayers", "BUNCH OF SHITTERS", 0x00001000) 
        return

    mmr = sum([int(i[0]) if i[0] != '3XXX' else 3000 for i in result]) / count
    avg = f"{count} players: {round(mmr)} ± 0"

    output = ""
    for res in result:
        mmr, name = res
        output += f'{name}: {mmr}\n'

    win32api.MessageBox(0, output, avg, 0x00001000)