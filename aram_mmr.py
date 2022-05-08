import re
from concurrent.futures import ThreadPoolExecutor
import requests
import win32api
from bs4 import BeautifulSoup
from fuzzywuzzy import process

#-----------------------------------------------------------------------------------------------------------------------
"""Aram MMR Preview"""
def get_mmr(name):
    r = requests.get('https://na.whatismymmr.com/api/v1/summoner?name=' + name)
    r = r.json()
    try:
        if r["ARAM"]["avg"]:
            return r["ARAM"]["avg"], r["ARAM"]["err"], name
    except:
        print("NO VALUE FOR", name)


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


