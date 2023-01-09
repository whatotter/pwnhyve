#!/usr/bin/env python
"""
auto install for artemis
"""
import subprocess, json, os

banner = """
    [1] install everything
"""

print(banner)

a = input(">")

if a == "1":
    print("""
are you sure? this will:

1. update the kernel and reboot the pi
2. setup dtoverlay and dwc2, adding to your /boot/config.txt
2.1. reboot the pi
3. create a bash file to start on startup for HID and mass storage capabilities from isticktoit
3.1 chmod that bash file and artemis' main file
4. edit your rc.local file to auto start the isticktoit gadget
4.1. make a systemd service to start artemis
5. make folder in mnt for mounting usb bin

confirm? [y/n]
    """)

    inp = input(">")

    if inp == "y" or len(inp) == 0:
        pass
    else:
        print("exiting..")
        quit()

    cwd = os.getcwd()

    with open("./core/installation/installation.json", "r") as f:
        currentJson = json.loads(f.read())

    if not currentJson["kernelUpdated"]:
        print("updating kernel")

        with open("./core/installation/installation.json", "r+") as f:
            js = json.loads(f.read())
            js["kernelUpdated"] = True
            f.write(json.dumps(js))

        subprocess.getstatusoutput("sudo BRANCH=next rpi-update")
        print("rebooting pi")
        subprocess.getstatusoutput("sudo reboot now")

    if not currentJson["dwc"]:
        print("setting up dtoverlay + dwc2")
        subprocess.getstatusoutput("echo \"dtoverlay=dwc2\" | sudo tee -a /boot/config.txt")
        subprocess.getstatusoutput("echo \"dwc2\" | sudo tee -a /etc/modules")

        with open("./core/installation/installation.json", "r+") as f:
            js = json.loads(f.read())
            js["dwc"] = True
            f.write(json.dumps(js))

        print("rebooting pi")
        subprocess.getstatusoutput("sudo reboot now")

    print("creating isticktoit usb gadget...")
    subprocess.getstatusoutput("sudo cp ./core/installation/artemisusb /bin/")
    subprocess.getstatusoutput("sudo chmod +x /bin/artemisusb")
    subprocess.getstatusoutput("sudo chmod +x ./main.py")

    print("editing rc.local file...")
    with open("/etc/rc.local", "r") as f:
        file = f.read().split('\n')

        # definitely a much better way of doing this
        file.insert(-2, "/bin/artemisusb")

    with open("/etc/rc.local", "w") as f:
        f.write('\n'.join(file))
        f.flush()

    print("setting up systemd service")

    with open("/bin/artemisStart", "w") as f:
        f.write(open("./core/installation/startup.sh", "r").read().replace("%cwd%", cwd))

    subprocess.getstatusoutput("sudo chmod +x /bin/artemisStart")

    with open("/etc/systemd/system/artemis.service", "w") as f:
        f.write(open("./core/installation/artemis.service", "r").read().replace("%cwd%", cwd))
        f.flush()

    subprocess.getstatusoutput("sudo systemctl enable artemis.service")

    print("making mnt dir")
    os.mkdir("/mnt/otterusb")

    print("done installing")


    

