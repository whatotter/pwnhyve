"""
based off of pwnagotchi's bettercap system but slightly modified (i am too lazy to write anything, thank you evilsocket)
"""
from core.utils import uStatus, uError
import requests
from requests.auth import HTTPBasicAuth
from subprocess import getoutput
from threading import Thread
from time import sleep


def decode(r):
    try:
        return r.json()
    except Exception as e:
        if r.status_code == 200:
            uError("error while decoding json: error='%s' resp='%s'" %
                   (e, r.text))
        else:
            err = "error %d: %s" % (r.status_code, r.text.strip())
            raise Exception(err)
        return r.text


class Client(object):
    def __init__(self, hostname='localhost', scheme='http', port=8081, username='user', password='pass', iface='wlan0mon', start=True):
        self.hostname = hostname
        self.scheme = scheme
        self.port = port
        self.username = username
        self.password = password
        self.url = "%s://%s:%d/api" % (scheme, hostname, port)
        self.auth = HTTPBasicAuth(username, password)

        if start:
            Thread(target=self.start, daemon=True,
                   kwargs={"iface": iface, }).start()

        self._wait_bettercap()

    def session(self):
        r = requests.get("%s/session" % self.url, auth=self.auth)
        return decode(r)

    def run(self, command):
        r = requests.post("%s/session" %
                          self.url, auth=self.auth, json={'cmd': command})
        return decode(r)

    def start(self, iface: str = "wlan0mon"):
        getoutput("sudo bettercap --iface %s -eval \"api.rest on\"" % (iface))

    def deauth(self, sta, throttle=0):

        try:
            self.run('wifi.deauth %s' % sta)
        except Exception as e:
            raise

        if throttle > 0:
            sleep(throttle)

    def associate(self, ap, throttle=0):

        try:
            self.run('wifi.assoc %s' % ap['mac'])
        except Exception as e:
            pass

        if throttle > 0:
            sleep(throttle)

    def getWifiJSON(self):
        r = requests.get("%s/session/wifi" % self.url, auth=self.auth)
        return decode(r)

    def clearWifi(self):
        return self.run("wifi.clear")

    def recon(self):
        return self.run("wifi.recon on")

    def hasHandshake(self, bssid):
        json = self.getWifiJSON()["aps"]

        for ap in json:
            if bssid == ap["mac"]:
                return ap["handshake"]

        return None

    def getPairs(self):
        json = self.getWifiJSON()

        aps = {}

        for ap in json["aps"]:
            clientMacs = []

            apMac = ap["mac"]
            clients = ap["clients"]

            
            for client in clients:
                clientMacs.append([client["mac"], client["vendor"]])

            aps[apMac] = [ap["hostname"], ap["encryption"], {
                "clients": clientMacs, 
                "freq": ap["frequency"], 
                "vendor": ap["vendor"],
                "channel": ap["channel"],
                }]

        return aps

    def _wait_bettercap(self):
        while True:
            try:
                requests.get("%s/session" % self.url, auth=self.auth)
                uStatus("bettercap avaialble")
                return
            except Exception:
                uStatus("waiting for bettercap API to be available ...")
                sleep(1)
