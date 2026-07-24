import random
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def simon(tpil:tinyPillow):
        quads = [
            {"key": "up",    "label": "UP",    "rect": [4, 4, 60, 30]},
            {"key": "down",  "label": "DOWN",  "rect": [4, 34, 60, 60]},
            {"key": "left",  "label": "LEFT",  "rect": [68, 4, 124, 30]},
            {"key": "right", "label": "RIGHT", "rect": [68, 34, 124, 60]},
        ]
        seq = []
        playerIdx = 0
        state = "showing"
        speed = 0.5

        def drawBoard(highlight=None):
            tpil.clear()
            for q in quads:
                x1, y1, x2, y2 = q["rect"]
                if highlight == q["key"]:
                    tpil.rect([x1, y1], [x2, y2])
                    tpil.text([(x1+x2)//2, (y1+y2)//2], q["label"], color="BLACK", fontSize=16, anchor="mm")
                else:
                    tpil.draw.rectangle([x1, y1, x2, y2], fill=0, outline=255)
                    tpil.text([(x1+x2)//2, (y1+y2)//2], q["label"], fontSize=16, anchor="mm")
            tpil.show()

        def showSequence():
            nonlocal playerIdx, speed
            for s in seq:
                drawBoard(s)
                tpil.waitWhileChkKey(0.05)
                tpil.waitWhileChkKey(speed)
                drawBoard(None)
                tpil.waitWhileChkKey(0.1)
            playerIdx = 0

        for _ in range(3):
            seq.append(random.choice(quads)["key"])
        showSequence()
        state = "input"

        while True:
            key = tpil.waitWhileChkKey(0.2)

            if state == "input":
                if key in ("up", "down", "left", "right"):
                    drawBoard(key)
                    tpil.waitWhileChkKey(0.15)

                    if key != seq[playerIdx]:
                        tpil.gui.toast("Wrong!\nScore: {}".format(len(seq) - 3), [10, 10], [118, 54])
                        return

                    playerIdx += 1
                    if playerIdx >= len(seq):
                        seq.append(random.choice(quads)["key"])
                        speed = max(0.15, speed - 0.03)
                        showSequence()
                        state = "input"
                    else:
                        drawBoard(None)
