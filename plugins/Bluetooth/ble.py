import json
import time
from core.bettercap.bettercap import Client
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow
from textwrap import wrap

bcap = Client()
bcap.bleRecon("on")
enumeratedDevices = []
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

def sortRSSIs(json:dict, top=5, identifier='mac'):
    rssipairs = []
    for device in json.get('devices', []):
        appended = False
        deviceRssi = device['rssi']
        deviceMac = device[identifier]

        if len(rssipairs) == 0: # need a starting point
            rssipairs.append(
                [deviceMac, deviceRssi]
            )
            continue

        for index, macpair in enumerate(rssipairs):
            iterMac, iterRssi = macpair

            if deviceRssi > iterRssi: # if our device RSSI is higher dBm than the current 'leaderboard' position holder
                rssipairs.insert(index, [deviceMac, deviceRssi]) # add our mac+rssi above them
                appended = True
                break

        if not appended:
            rssipairs.append([deviceMac, deviceRssi])

    return rssipairs[:top]

def split22s(s):
    return [s[i:i+2] for i in range(0, len(s), 2)]

class PWNBluetooth(BasePwnhyvePlugin):
    _icons = {
        "Enumerate_Clients": "./core/icons/wififolder.bmp",
        "BLE_Write": "./core/icons/clipboard.bmp",
        "Graph_RSSIs": "./core/icons/graph.bmp"
    }
    
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

            menu.draw(
                '\n'.join(text[sliceIndex:]),
                "{}/{}".format(chosenIndex+1, len(clientList))
            )

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

    def BLE_Write(tpil:tinyPillow):
        global enumeratedDevices
        while True:
            clients = bcap.getBluetoothClients()

            sortedName = sortRSSIs(clients, identifier='name')
            sortedMac = sortRSSIs(clients, identifier='mac')

            choice = tpil.gui.menu(["Refresh"] + ["{} ({}) ({})".format(x[0], x[1], sortedMac[sortedName.index(x)][0]) for x in sortedName])
            if choice == None: break
            elif choice == "Refresh": pass
            else:
                index = ["{} ({}) ({})".format(x[0], x[1], sortedMac[sortedName.index(x)][0]) for x in sortedName].index(choice)
                mac = sortedMac[index][0]
                tpil.clear()


                if mac not in enumeratedDevices:
                    print("enumerating..")
                    bcap.run("ble.enum {}".format(mac))
                    enumeratedDevices.append(mac)
                    time.sleep(0.5) # wait for enumeration

                devices = bcap.getBluetoothClients()["devices"]

                targetDevice = None

                for device in devices:
                    if mac == device['mac']:
                        targetDevice = device
                        break

                #open("dump.json", "w").write(json.dumps(targetDevice, indent=4))

                bleEnumerate = targetDevice['services']
                bleEnumDict = {}

                for value in bleEnumerate:
                    bleEnumDict[value['uuid']] = value

                menuDictionary = {}
                for uuid, value in bleEnumDict.items():
                    name = "{} ({})".format(value["name"], uuid)
                    menuDictionary[name] = uuid

                while True:
                    enumChoice = tpil.gui.menu(menuDictionary)
                    if enumChoice == None:
                        break

                    charDict = {}
                    characteristics = bleEnumDict[enumChoice]["characteristics"]
                    for value in characteristics:
                        charDict[value['uuid']] = value

                    menuDictionary.clear()
                    for uuid, value in charDict.items():
                        name = "{} ({})".format(value["name"], uuid)
                        menuDictionary[name] = uuid

                    while True:
                        characteristicChoice = tpil.gui.menu(menuDictionary)
                        if characteristicChoice == None:
                            break

                        chosenCharacteristic = charDict[characteristicChoice]

                        while True:
                            isWrite = tpil.gui.menu(["{}: {}".format(x,y) for x,y in chosenCharacteristic.items()] + [" ", "Write"])
                            
                            if isWrite == "Write":
                                pass
                            elif isWrite == None:
                                break
                            else:
                                key = isWrite.split(":",1)[0]
                                sc = tpil.gui.screenConsole(tpil)
                                sc.text = chosenCharacteristic[key]
                                sc.update()
                                sc.exit()

                                tpil.waitForKey()         

    def Graph_RSSIs(tpil):

        """
        rssis = [
            ["11:22:33:44:55:66", -3],
            ["11:22:33:44:55:66", -20],
            ["22:33:44:55:66:77", -22],
            ["22:33:44:55:66:77", -30],
            ["22:33:44:55:66:77", -34],
            ["22:33:44:55:66:77", -40],
            ["22:33:44:55:66:77", -44],
            ["33:44:55:66:77:88", -54],
        ]
        """

        time.sleep(0.1)

        while True:
            clients = bcap.getBluetoothClients()
            rssis = sortRSSIs(clients)

            tpil.clear()

            barMargin = 2
            barWidth = 12
            xCoord = 16
            legendXCoord = 0
            barTopPadding = 8

            highestRSSI = rssis[0][1]
            for macpair in rssis:
                barHeight = (highestRSSI-macpair[1]) + barTopPadding
                macAddr = macpair[0]
                index = rssis.index(macpair)

                tpil.rect((xCoord, barHeight), (xCoord+barWidth, tpil.disp.height))
                tpil.text((xCoord+2, barHeight+2), # stupidly complicated to draw text vertically 
                        '\n'.join(split22s(macAddr.replace(":", ""))),
                        color='BLACK', fontSize=14)
                
                #tpil.rect((legendXCoord+8, barHeight), (xCoord+8+4, barHeight))
                previousRSSI = rssis[index-1][1] if index-1 >= 0 else macpair[1]

                if 4 >= previousRSSI - macpair[1] and previousRSSI != macpair[1]:
                    pass
                else:
                    tpil.text((legendXCoord-1, barHeight-4), str(macpair[1]), fontSize=14)
                
                xCoord += barWidth+barMargin

            tpil.show()
            
            if tpil.checkIfKey(): break
            time.sleep(0.1)