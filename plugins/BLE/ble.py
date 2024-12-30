import time
from core.bettercap.bettercap import Client
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow
from textwrap import wrap

bcap = Client()
bcap.bleRecon("on")

clientTextForms = {}

def textlifyClients(json:dict):
    global clientTextForms
    """
    {
        'devices': [
            {
                'last_seen': '2024-10-07T00:40:49.091614296Z', 
                'name': '', 'mac': 'XX:XX:XX:XX:XX:XX', 
                'alias': '', 'vendor': 'HP Inc.', 'rssi': -63, 
                'connectable': True, 'flags': 'BR/EDR Not Supported', 
                'services': []
            }, 
            {
                'last_seen': '2024-10-07T00:40:48.401293382Z', 
                'name': '', 'mac': 'XX:XX:XX:XX:XX:XX', 'alias': '', 
                'vendor': 'Google', 'rssi': -82, 'connectable': False, 
                'flags': '', 'services': []
            }, 
            {
                'last_seen': '2024-10-07T00:40:47.975035701Z', 
                'name': 'CMF Watch Pro 2-E82D', 'mac': 'XX:XX:XX:XX:XX:XX', 
                'alias': '', 'vendor': 'Nothing Technology Limited', 
                'rssi': -76, 'connectable': True, 'flags': '', 'services': []
            }
        ]
    }
    """

    for device in json.get('devices', []):
        text = ["{}: {}".format(x,
                                '\n'.join(wrap(str(y), width=20))
                                ) for x,y in device.items()] # straight up just dump the whole dictionary into a string

        clientTextForms[device['mac']] = text

    return clientTextForms

def sortRSSIs(json:dict, top=5):
    rssipairs = []

    for device in json.get('devices', []):
        deviceRssi = device['rssi']
        deviceMac = device['mac']

        if len(rssipairs) == 0: # need a starting point
            rssipairs.append(
                [deviceMac, deviceRssi]
            )
            continue

        for index, macpair in enumerate(rssipairs):
            iterMac, iterRssi = macpair

            if deviceRssi > iterRssi: # if our device RSSI is higher dBm than the current 'leaderboard' position holder
                rssipairs.insert(index, [deviceMac, deviceRssi]) # add our mac+rssi above them

    return rssipairs[:top]

def split22s(s):
    return [s[i:i+2] for i in range(0, len(s), 2)]

class PWNBluetooth(BasePwnhyvePlugin):
    def Enumerate_Clients(tpil:tinyPillow):
        chosenIndex = 0
        sliceIndex = 0
        menu = tpil.gui.carouselMenu(tpil)

        while True:
            a = bcap.getBluetoothClients()
            clientList = textlifyClients(a)

            # sanity checks
            if 0 > chosenIndex: chosenIndex = 0
            if chosenIndex > len(clientList)-1: chosenIndex = len(clientList)-1

            # pick and draw
            for index,key in enumerate(clientList): # there's fs a better way to do this
                if index == chosenIndex:
                    mac = key
                    text = clientList[mac]

            tpil.clear()
            menu.draw(
                '\n'.join(text[sliceIndex:]),
                "{}/{}".format(chosenIndex+1, len(clientList)), wrap=False
            )
            tpil.show()

            # user input
            key = tpil.getKey(debounce=True)
            if key == 'right': # next client
                chosenIndex += 1
            elif key == 'left': # back 1 client
                chosenIndex -= 1
            elif key == '3': # exit
                break
            elif key == 'up': # scroll up on the text
                sliceIndex -= 1
                if 0 > sliceIndex: sliceIndex = 0
            elif key == 'down': # scroll down on the text
                if len(text)-1 == sliceIndex: # scrolled down far enough, no more
                    pass
                else:
                    sliceIndex += 1
            elif key == False: # no key pressed, update
                time.sleep(0.1)

    def Graph_RSSIs(tpil):
        #rssis = sortRSSIs(bcap.getBluetoothClients())
        rssis = [
            ["11:22:33:44:55:66", -20],
            ["22:33:44:55:66:77", -22],
            ["33:44:55:66:77:88", -54],
        ]
        bars = 5
        barMargin = 2
        barWidth = 12
        xCoord = 2
        barTopPadding = 8

        tpil.clear()

        highestRSSI = rssis[0][1]
        for macpair in rssis:
            barHeight = (highestRSSI-macpair[1]) + barTopPadding
            macAddr = macpair[0]

            tpil.rect((xCoord, barHeight), (xCoord+barWidth, tpil.disp.height))
            tpil.text((xCoord+2, barHeight+2), # stupidly complicated to draw text vertically 
                      '\n'.join(split22s(macAddr.replace(":", ""))),
                      color='BLACK', fontSize=14)
            
            xCoord += barWidth+barMargin

        print("show")
        tpil.show()
        print("show")

        tpil.waitForKey()