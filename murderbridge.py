import time
from traceback import print_tb
import requests
import webbrowser
from lcu_driver import Connector
import cassiopeia as cass
import pickle
import os 

conn = Connector()

@conn.ready
async def murder_bridge(conn):
    
    champ = await conn.request('GET', '/lol-champ-select/v1/current-champion') 
    champ = await champ.json()

    champ_list = []
    if not os.path.exists("champs.pickle") or time.time() - os.path.getmtime("champs.pickle") > 304800:
        versions = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()
        champ_list = {champ.id: champ.name for champ in cass.core.staticdata.Champions(region='NA', version=versions[0])}
        pickle.dump(champ_list, open("champs.pickle",'wb'))
    else:
        champ_list = pickle.load(open("champs.pickle",'rb'))


    if type(champ) == int and champ in champ_list:
        webbrowser.open(f'https://murderbridge.com/Champion/{champ_list[champ]}/')



@conn.close
async def disconnect(_):
    await conn.stop() 
    quit()

conn.start()
