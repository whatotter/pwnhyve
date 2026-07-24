import os

from core.lib.rpitx.rpitx import rpitx, rpitxTypes, PiFMRds
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow
import time
import socket
import tempfile

fm = PiFMRds()
iq = rpitx()

URH_HOST = "0.0.0.0"
URH_PORT = 1234

class URHLink():
    # TODO: finish this
    def recieveSocket():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((URH_HOST, URH_PORT))
            server.listen(1)
            print(f"Listening for URH on port {URH_PORT}...")

            while True:
                conn, addr = server.accept()
                print(f"URH connected from {addr}")

                # Write IQ to temp file then pass to rpitx
                with tempfile.NamedTemporaryFile(
                    suffix='.iq', delete=False
                ) as f:
                    tmp = f.name
                    while chunk := conn.recv(65536):
                        f.write(chunk)

                conn.close()
                print(f"Received, transmitting at {freq_khz}kHz...")

                # TRANSMIT i/q

                os.unlink(tmp)
                print("Done, waiting for next transmission...")

class PWN_Rpitx(BasePwnhyvePlugin):
    _icons = {
        "Play_FM_Radio": "./core/icons/routeremit.bmp",
    }
        
    def Play_FM_Radio(tpil:tinyPillow):
        audio = "./addons/fm_audio/" + tpil.gui.menu(list(filter(lambda x: x.endswith(".wav"), os.listdir("./addons/fm_audio"))))
        if audio == None: return

        frequency = tpil.gui.slider("FM Frequency", minimum=90, maximum=110, 
                                    start=102.5, step=0.1, bigstep=1).draw()
        

        sc = tpil.gui.screenConsole()
        sc.addText("Hit any key to stop\n\n\n" + "Playing FM @ {}\n{}".format(frequency, audio))
        time.sleep(0.1) # finish writes to gpio

        fm.freq = frequency

        fm.play(audio)

        tpil.waitForKey()

        fm.stop()

    def URH_Transmitter(tpil:tinyPillow):
        sc = tpil.gui.screenConsole()
        sc.addText("URH @ 0.0.0.0:1234")
        time.sleep(0.1)

        tpil.waitForKey()