import random
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow
from collections import deque

class Plugin(BasePwnhyvePlugin):
    def frogger(tpil:tinyPillow):
        frogX = 64
        frogW, frogH = 6, 6
        score = 0
        frogRow = 6
        moveCooldown = 0

        def makeLane():
            t = random.choices(
                ["grass", "road", "train", "water"],
                weights=[30, 30, 5, 25]
            )[0]
            lane = {"type": t, "cars": [], "logs": [], "trainX": -20}
            if t == "road":
                n = random.randint(1, 3)
                for _ in range(n):
                    lane["cars"].append([random.randint(-20, 128), random.choice([-2, -1, 1, 2]) * random.randint(1, 2)])
            elif t == "water":
                n = random.randint(1, 2)
                for _ in range(n):
                    lane["logs"].append([random.randint(-30, 128), random.choice([1, 2])])
            elif t == "train":
                lane["trainX"] = random.choice([-30, 148])
                lane["trainDir"] = random.choice([-4, 4])
            return lane

        def grassLane():
            return {"type": "grass", "cars": [], "logs": [], "trainX": -20}

        lanes = deque()
        for _ in range(4):
            lanes.append(grassLane())
        for _ in range(3):
            lanes.appendleft(makeLane())

        while True:
            key = tpil.checkIfKey()
            if key == False:
                key = None

            if moveCooldown <= 0:
                if key == "up" and frogRow > 0:
                    frogRow -= 1
                    score += 1
                    moveCooldown = 5
                    if frogRow <= 3:
                        lanes.pop()
                        lanes.pop()
                        a = makeLane()
                        b = makeLane()
                        lanes.appendleft(a)
                        lanes.appendleft(b)
                        for i in range(min(len(lanes) - 1, 3)):
                            if lanes[i]["type"] == "water" and lanes[i + 1]["type"] != "grass":
                                lanes[i + 1] = grassLane()
                        frogRow += 2
                elif key == "left" and frogX > 0:
                    frogX -= 8
                    moveCooldown = 5
                elif key == "right" and frogX < 122:
                    frogX += 8
                    moveCooldown = 5
            else:
                moveCooldown -= 1

            for lane in lanes:
                if lane["type"] == "road":
                    for car in lane["cars"]:
                        car[0] += car[1]
                        if car[0] > 138:
                            car[0] = -20
                        elif car[0] < -30:
                            car[0] = 138
                elif lane["type"] == "water":
                    for log in lane["logs"]:
                        log[0] += log[1]
                        if log[0] > 148:
                            log[0] = -30
                        elif log[0] < -40:
                            log[0] = 148
                elif lane["type"] == "train":
                    lane["trainX"] += lane["trainDir"]
                    if lane["trainX"] > 150:
                        lane["trainX"] = -40
                    elif lane["trainX"] < -50:
                        lane["trainX"] = 150

            lane = lanes[frogRow]
            frogY = 8 + frogRow * 8
            hit = False
            if lane["type"] == "road":
                for car in lane["cars"]:
                    if car[0] < frogX + frogW and car[0] + 10 > frogX:
                        hit = True
                        break
            elif lane["type"] == "train":
                cx, cw = lane["trainX"], 30
                if cx < frogX + frogW and cx + cw > frogX:
                    hit = True
            elif lane["type"] == "water":
                onLog = False
                for log in lane["logs"]:
                    if log[0] < frogX + frogW and log[0] + 14 > frogX:
                        frogX += log[1]
                        frogX = max(0, min(122, frogX))
                        onLog = True
                        break
                if not onLog:
                    hit = True

            if hit:
                tpil.gui.toast("Game Over\nScore: {}".format(score), [10, 10], [118, 54])
                return

            tpil.clear()
            for i, lane in enumerate(lanes):
                y = 8 + i * 8
                if lane["type"] == "road":
                    for dx in range(0, 128, 12):
                        tpil.rect([dx, y + 3], [dx + 4, y + 4])
                    for car in lane["cars"]:
                        tpil.rect([car[0], y], [car[0] + 10, y + 7])
                elif lane["type"] == "train":
                    cx = lane["trainX"]
                    tpil.rect([cx, y], [cx + 30, y + 7])
                    tpil.rect([0, y], [128, y])
                elif lane["type"] == "water":
                    for cx in range(0, 128, 2):
                        for cy in range(0, 8, 2):
                            if (cx // 2 + cy // 2 + i) % 2 == 0:
                                tpil.rect([cx, y + cy], [cx, y + cy])
                    for log in lane["logs"]:
                        tpil.rect([log[0], y + 2], [log[0] + 14, y + 5], color="BLACK")

            tpil.rect([frogX, frogY], [frogX + frogW, frogY + frogH])
            tpil.text([2, 2], "Score: {}".format(score), fontSize=16)
            tpil.show()
