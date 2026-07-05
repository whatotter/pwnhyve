import random
import time
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def rhythm(tpil:tinyPillow):
        lanes = [
            {"key": "up",    "y": 6,  "label": "UP"},
            {"key": "right", "y": 20, "label": "R>"},
            {"key": "down",  "y": 34, "label": "DN"},
            {"key": "left",  "y": 48, "label": "<L"},
        ]
        notes = []
        score = 0
        missed = 0
        speed = 3
        spawnTimer = 0
        spawnInterval = 40
        combo = 0
        frame = 0

        while True:
            key = tpil.checkIfKey()
            if key == False:
                key = None

            if key in ("up", "down", "left", "right"):
                hit = False
                for n in notes[:]:
                    if n["key"] == key and 6 < n["x"] < 22:
                        dist = abs(n["x"] - 14)
                        pts = max(10 - dist, 1)
                        score += pts
                        combo += 1
                        notes.remove(n)
                        hit = True
                        break
                if not hit:
                    combo = 0

            spawnTimer += 1
            if spawnTimer >= max(15, spawnInterval - score // 5):
                spawnTimer = 0
                lane = random.choice(lanes)
                notes.append({"key": lane["key"], "x": 124, "y": lane["y"]})

            for n in notes[:]:
                n["x"] -= speed
                if n["x"] < 0:
                    notes.remove(n)
                    missed += 1
                    combo = 0

            if missed >= 5:
                tpil.gui.toast("Game Over\nScore: {}".format(score), [10, 10], [118, 54])
                return

            speed = 3 + score // 30

            tpil.clear()
            for lane in lanes:
                tpil.rect([14, lane["y"]], [22, lane["y"] + 10])
                tpil.text([2, lane["y"] + 2], lane["label"], fontSize=16)
            for n in notes:
                tpil.rect([n["x"], n["y"] + 2], [n["x"] + 8, n["y"] + 8])
            tpil.text([80, 2], "S:{}".format(score), fontSize=16)
            tpil.text([80, 12], "C:{}".format(combo), fontSize=16)
            tpil.show()
            frame += 1
