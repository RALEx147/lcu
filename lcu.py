import subprocess
import time
import keyboard
from lcu_driver import Connector
from aram_mmr import display_mmr
 
conn = Connector()
subprocess.call(["C:\Program Files\AutoHotkey\AutoHotkey.exe", "C:\\Users\\rale\\Documents\\Programming\\murderbridge.ahk"])

@conn.ws.register('/lol-champ-select/v1/session', event_types=('CREATE',))
async def connect(conn, event):
    champ_select = event.data
    await display_mmr(champ_select, conn)



#-----------------------------------------------------------------------------------------------------------------------
"""Accept Queue"""

async def accept(c):
    if keyboard.read_key(): 
        await c.request('POST', '/lol-matchmaking/v1/ready-check/accept') 


@conn.ws.register('/lol-matchmaking/v1/ready-check')
async def ready(connection, event):
    data = event.data 
    if data and data['timer'] == 0.0 and data['state'] == "InProgress":
        await accept(connection)

@conn.close
async def disconnect(_):
    await conn.stop() 
    quit()

conn.start()
