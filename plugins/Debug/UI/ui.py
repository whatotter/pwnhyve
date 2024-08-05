"""
my lil ui playground
"""
from core.plugin import BasePwnhyvePlugin
import threading
import random, time
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
    def screenConsole(draw, disp, image, GPIO):
        a = disp.gui.screenConsole(draw, disp, image, GPIO, "abcd")
        threading.Thread(target=a.start, daemon=True).start()

        a.text = "hello world!" + "\n" + "text and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it and a lot of it"

        disp.waitForKey()

        a.text = ""
        while True:
            a.addText("i am ticket #{}. woohoo!".format(random.randint(10,99)))
            
            z = disp.waitWhileChkKey(1)
            if z == disp.pinout["KEY_LEFT_PIN"]:
                a.text = ""
            elif z == False:
                pass
            else:
                break
            

        a.exit()

    def screenConsole2(draw,disp,image,GPIO):

        a = disp.gui.screenConsole(draw, disp, image, GPIO, "abcd")
        threading.Thread(target=a.start, daemon=True).start()
        
        a.text = (scText("i like lucki\nand fornite\n and roblox\n12345678", "@{}hz | ASYNC-OOK".format("303.91")))

        disp.waitForKey()
        a.exit()