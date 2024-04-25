import webbrowser
from lcu_driver import Connector
from aram_mmr import display_mmr, display_high_mmr
import asyncio

conn = Connector()

@conn.ready
async def display_mmr_now(conn):

    champ_select = await conn.request('get', '/lol-champ-select/v1/session/')
    champ_select = await champ_select.json()

    if 'httpStatus' in champ_select and champ_select['httpStatus'] == 404:
        return
        
    await display_high_mmr(champ_select, conn)
    quit()


    
@conn.close
async def disconnect(_):
    await conn.stop() 
    quit()

conn.start()
