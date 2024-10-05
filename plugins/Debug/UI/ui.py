"""
my lil ui playground
"""
from core.plugin import BasePwnhyvePlugin
import threading
import random
from core.plugin import BasePwnhyvePlugin 


sctext = ""
def scText(text, caption, maxln=6):
    global sctext

    s = (sctext+"\n"+str(text)).strip().split("\n")
    lines = len(s)

    if lines > maxln-1:
        while len(s) > maxln-1:
            print("pop!")
            s.pop(0)
    elif lines != maxln-1:
        while len(s) != maxln-1:
            s.append("")

    s.append(caption)

    return '\n'.join(s)

class PWNTestOne(BasePwnhyvePlugin):
    def screenConsole(tpil):
        a = tpil.gui.screenConsole(tpil)

        a.text = "hello world!" + "\n" + "text and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it"

        tpil.waitForKey()

        a.text = ""
        while True:
            a.addText("i am ticket #{}. woohoo!".format(random.randint(10,99)))
            
            z = tpil.waitWhileChkKey(1)
            if z == tpil.pinout["left"]:
                a.text = ""
            elif z == False:
                pass
            else:
                break
            

        a.exit()

    def screenConsole2(tpil):

        a = tpil.gui.screenConsole(tpil)
        threading.Thread(target=a.start, daemon=True).start()
        
        a.text = (scText("i like lucki\nand fornite\n and roblox\n12345678", "@{}hz | ASYNC-OOK".format("303.91")))

        tpil.waitForKey()
        a.exit()

    def legend(tpil):
        a = tpil.gui.keyLegend(tpil, {"right": "next", "press": "ok", "left": "back", "1": "record"})

        tpil.clear()

        a.draw()

        tpil.show()

        tpil.waitForKey()