import re
from concurrent.futures import ThreadPoolExecutor
import requests
import win32api
from bs4 import BeautifulSoup
from fuzzywuzzy import process

"""
    Get MMR for one Summoner usng whatismymmr

    @param name: Summoner name string
    @return: MMR int, MMR std int, name string
    @raise None: No aram value for this summoner
""" 
def get_mmr(name):
    r = requests.get('https://na.whatismymmr.com/api/v1/summoner?name=' + name)
    r = r.json()
    try:
        if r["ARAM"]["avg"]:
            return r["ARAM"]["avg"], r["ARAM"]["err"], name
    except:
        print("NO VALUE FOR", name)


"""
    Get Aram Leaderboard from aram.moe

    @return: Dirty Doughnut: ("16", "3492 ± 0")
"""
def get_ranks():
    output = {}
    page = requests.get("https://aram.moe/")
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find_all(class_="player-container")
    for i in results:
        p = re.compile(r'<div class="player-container"><span class="num">(.+)</span><span class="name">(.+)</span><span class="mmr">(.+)</span></div>')
        m = p.match(str(i))
        if m is not None:
            output[m.group(2)] = (m.group(1), m.group(3))
    return output


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
async def display_mmr(champ_select, conn):
    
    ids = [i["summonerId"] for i in champ_select["myTeam"] if i != 0]

    names = []
    for i in ids:
        name = await conn.request('get', '/lol-summoner/v1/summoners/' + str(i))
        name = await name.json()
        names.append(name["displayName"])

    result = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        result = list(pool.map(get_mmr, names))


    result = [i for i in result if i]
    count = len(result)
    
    if count == 0:
        win32api.MessageBox(0, "", "BUNCH OF SHITTERS", 0x00001000) 
        return

    mmr = sum([i[0] for i in result]) / count
    err = sum([i[1] for i in result]) / count

    avg = f"{count} players: {round(mmr)} ±{round(err)}"

    ranks = []
    top500 = get_ranks()

    lowest500 = min([int(i[0]) for i in top500.values()])
    for res in result:
        mmr, err, name = res
        ranking = "XXX"
        if name in top500:
            ranking = f'{int(top500[name][0]):03d}'
        else:
            fuzzy_name = process.extractOne(name, top500.keys())
            if mmr >= lowest500 and fuzzy_name in top500:
                print("fuzzy", fuzzy_name, mmr, ">", lowest500)
                ranking = f'{int(top500[name][0]):03d}'
        
        ranks.append([ranking, name, mmr, err])
    
    output = ""
    for i in sorted(ranks, key=lambda x: x[2], reverse=True):
        output += f'#{i[0]} {i[1]}: {i[2]} ± {i[3]}\n'
    
    win32api.MessageBox(0, output, avg, 0x00001000) 


