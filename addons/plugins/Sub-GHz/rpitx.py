from core.rpitx.rpitx import rpitx, rpitxTypes, PiFMRds
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow
import time

fm = PiFMRds()
iq = rpitx()

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
