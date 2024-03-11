#l0guecow ported applejuice's BLE plugin to pwnhyve
#sudo apt-get install bluetooth libbluetooth-dev
#sudo python3 -m pip install pybluez
#pip install git+https://github.com/airgproducts/pybluez2
#$ pip install bleak
#pip install git+https://github.com/pybluez/pybluez.git#egg=pybluez
from core.plugin import BasePwnhyvePlugin

import subprocess

class PwnhyvePlugin(BasePwnhyvePlugin):
    def launch_proximity_spoofing(self):
        try:
            subprocess.run(["python", "./app.py", "-r", "-i", "20"])
        except Exception as e:
            print(f"An error occurred while launching the script: {e}")

    def display_menu(self):
        print("1. Launch Proximity Pairing Notification Spoofing")
        print("2. Other options...")  # Add other menu options as needed

    def handle_menu_selection(self, selection):
        if selection == 1:
            self.launch_proximity_spoofing()
        elif selection == 2:
            # Handle other menu options...
            pass
        else:
            print("Invalid selection. Please choose a valid option.")