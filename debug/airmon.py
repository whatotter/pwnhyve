import json
import time
import netifaces as nf
from scapy.all import RandMAC, RadioTap, Dot11, Dot11Beacon, Dot11Elt, sendp, sniff, Dot11ProbeResp
from subprocess import getoutput

class airmon:
    def toggleMonitorMode(iface):

        isInMonitorMode, monitorModeInterface = airmon.checkIfMonitorMode(iface)
        
        if not isInMonitorMode: # isn't in monitor mode
            a = getoutput("sudo /usr/sbin/airmon-ng start {} | grep \"mac80211 monitor mode\"".format(iface)).strip().split("[phy")[-1]
            rmStr = ''.join(a[:2])
            monIface = a.replace(")", "").replace(rmStr, "") # ooga booga i hate regex so im gonna use the .strip() and .split() and .replace() !!!!!!!!!

            return {
                "interface": monIface,
                "monitorMode": True
            }
        
        else: # in monitor mode
            a = getoutput("sudo /usr/sbin/airmon-ng stop {} | grep \"mac80211 station mode\"".format(monitorModeInterface)).strip().split("[phy")[-1]
            rmStr = ''.join(a[:2])
            monIface = a.replace(")", "").replace(rmStr, "") # ooga booga i hate regex so im gonna use the .strip() and .split() and .replace() !!!!!!!!!

            return {
                "interface": monIface,
                "monitorMode": False
            }
        
    def startMonitorMode(iface):

        isInMonitorMode, monitorModeInterface = airmon.checkIfMonitorMode(iface)

        if isInMonitorMode:
            print("[WIFI] {} was already in monitor mode (first check)".format(iface))
            
            return {
                "interface": monitorModeInterface,
                "monitorMode": True
            }
        

        print("[WIFI] attempting to set {} in monitor mode".format(iface))

        getoutput("sudo /usr/sbin/airmon-ng check kill")
        out = getoutput("sudo /usr/sbin/airmon-ng start {}".format(iface)).split("\n")
        
        a = None

        for x in out:
            if "mac80211 monitor mode" in x:
                a = x.strip().split("[phy")[-1]
            else:
                if "ERROR" in x:
                    a = None
                    code = x.split(" ")[-1]
                    print("[WIFI] error putting in monitor mode: {}".format(code))

                    return {
                        "interface": None, # not changed
                        "monitorMode": False
                    }


        rmStr = ''.join(a[:2])
        monIface = a.replace(")", "").replace(rmStr, "") # ooga booga i hate regex so im gonna use the .strip() and .split() and .replace() !!!!!!!!!

        print("[WIFI] success")

        return {
            "interface": monIface,
            "monitorMode": True
        }
        
        
    def stopMonitorMode(iface):
        isInMonitorMode, monitorModeInterface = airmon.checkIfMonitorMode(iface)

        if isInMonitorMode:
            a = getoutput("sudo /usr/sbin/airmon-ng stop {} | grep \"mac80211 monitor mode\"".format(monitorModeInterface)).strip().split("[phy")[-1]
            rmStr = ''.join(a[:2])
            monIface = a.replace(")", "").replace(rmStr, "") # ooga booga i hate regex so im gonna use the .strip() and .split() and .replace() !!!!!!!!!

            b = getoutput("sudo /usr/bin/systemctl start NetworkManager")

            return {
                "interface": monIface,
                "monitorMode": False
            }
        
        else:
            return {
                "interface": monIface, # not changed
                "monitorMode": False
            }
            
    def checkIfMonitorMode(iface):
        out = nf.interfaces()
        if "{}mon".format(iface) in out:
            print("[WIFI] {} is managed mode due to {}mon existing".format(iface, iface))
            return (True, "{}mon".format(iface)) # mon mode exists
            
        return (False, None)
    
def genFrame(ssid):
    randMac = RandMAC()
    dot11Frame = Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2=randMac, addr3=randMac)
    beac = Dot11Beacon(cap="ESS+privacy")
    elt = Dot11Elt(ID="SSID", info=ssid, len=len(ssid))

    return RadioTap()/dot11Frame/beac/elt


interface = airmon.startMonitorMode("wlan0")["interface"]

print("[+] mon mode enabled on interface {}".format(interface))

testFrame = genFrame("test frame")
for x in range(120):
    print("on frame {}".format(x))
    sendp(testFrame, iface=interface, verbose=1, count=1)
    time.sleep(0.25)

#airmon.stopMonitorMode(interface)
