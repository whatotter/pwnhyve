from core.utils import redir, config
import threading
import json, base64

import asyncio
import websockets.exceptions
from websockets.server import serve

class BaseDisplayDriver():
    """reserved"""
    def __init__(self) -> None:
        
        pass
    
class sockStream:
    connection = None
    mostRecentImage = None
    mostRecentButton = None
    resendImage = False
    queue = []

    async def asyncStart():
        async with serve(sockStream.handle, "0.0.0.0", 8765):
            await asyncio.Future()  # run forever

    def start():

        if not config["vnc"]["enableVNC"]:
            print('vnc disabled')
            return
        
        while True:
            print("[VNC] READY FOR CONNECTIONS.")
            asyncio.run(sockStream.asyncStart())

    async def handle(websocket):
        while True:
            if len(sockStream.queue) != 0 or sockStream.resendImage:

                if not sockStream.resendImage:
                    frame = sockStream.queue[-1]
                    sockStream.queue.clear()
                else:
                    frame = sockStream.mostRecentImage
                    sockStream.resendImage = False

                await websocket.send(json.dumps({
                    "frame": frame.decode('ascii'),
                    "log": base64.b64encode(
                                    ''.join(redir.log).encode('ascii')
                                    ).decode('ascii')
                }))

                redir.log = []

            try:
                a = await asyncio.wait_for(websocket.recv(), 0.1)
            except (websockets.exceptions.ConnectionClosedOK):
                print("[VNC] Client closed connection")
                return
            except (websockets.exceptions.ConnectionClosedError):
                print("[VNC] Client closed connection abruptly")
                return
            except (TimeoutError, asyncio.exceptions.TimeoutError):
                a = None

            if a != None:
                if a != "R":
                    sockStream.mostRecentButton = a
                else:
                    print("[VNC] CONNECTION ESTABLISHED")
                    sockStream.resendImage = True # when a new connection is established, send the current screen image
    

def checkSocketINput():
    gpio = sockStream.mostRecentButton
    sockStream.mostRecentButton = None

    #open("/tmp/socketGPIO", "w").write("") # leave blank (worst way to do this probably)
    if gpio == "" or gpio == None:
        return False
    else:
        if gpio in ["up", "left", "right", "down", "1", "2", "3", "press"]:
            return gpio
        
threading.Thread(target=sockStream.start, daemon=True).start()