import random
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def pacman(tpil:tinyPillow):
        T = 8
        COLS, ROWS = 16, 8
        maze = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,1,0,0,0,0,0,0,1,0,0,0,0,1],
            [1,0,0,1,0,1,0,0,0,0,1,0,1,0,0,1],
            [1,0,0,0,0,1,0,0,0,0,0,0,1,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,1],
            [1,0,0,1,0,1,0,0,0,0,1,0,1,0,0,1],
            [1,0,0,1,0,0,0,0,0,0,1,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        ]
        dots = [[c, r] for r in range(ROWS) for c in range(COLS) if maze[r][c] == 0]
        pacX, pacY = 1, 1
        dirs = {"up": (0,-1), "down": (0,1), "left": (-1,0), "right": (1,0)}
        moveDir = (1, 0)
        nextDir = (1, 0)
        ghosts = [
            {"x": 7, "y": 3, "dir": (0,0), "color": "WHITE"},
            {"x": 8, "y": 4, "dir": (0,0), "color": "WHITE"},
            {"x": 7, "y": 4, "dir": (0,0), "color": "WHITE"},
        ]
        score = 0
        lives = 3
        frame = 0
        superMode = 0
        moveTimer = 0

        def canMove(x, y, d):
            nx, ny = x + d[0], y + d[1]
            return 0 <= nx < COLS and 0 <= ny < ROWS and maze[ny][nx] != 1

        def ghostMove(g):
            opts = [(0,1),(0,-1),(1,0),(-1,0)]
            random.shuffle(opts)
            for d in opts:
                if canMove(g["x"], g["y"], d) and (d[0] != -g["dir"][0] or d[1] != -g["dir"][1]):
                    g["dir"] = d
                    break
            g["x"] += g["dir"][0]
            g["y"] += g["dir"][1]

        while True:
            key = tpil.checkIfKey()
            if key == False:
                key = None

            if key in dirs:
                nextDir = dirs[key]
            if canMove(pacX, pacY, nextDir):
                moveDir = nextDir

            moveTimer += 1
            if moveTimer >= 4:
                moveTimer = 0
                if canMove(pacX, pacY, moveDir):
                    pacX += moveDir[0]
                    pacY += moveDir[1]
                    if [pacX, pacY] in dots:
                        dots.remove([pacX, pacY])
                        score += 1

            if frame % 6 == 0:
                for g in ghosts:
                    ghostMove(g)

            for g in ghosts:
                if g["x"] == pacX and g["y"] == pacY:
                    if superMode > 0:
                        g["x"], g["y"] = 7, 3
                        score += 5
                        superMode = 30
                    else:
                        lives -= 1
                        if lives == 0:
                            tpil.gui.toast("Game Over\nScore: {}".format(score), [10, 10], [118, 54])
                            return
                        pacX, pacY = 1, 1
                        for g2 in ghosts:
                            g2["x"], g2["y"] = 7, 4

            if not dots:
                tpil.gui.toast("You Win!\nScore: {}".format(score), [10, 10], [118, 54])
                return

            if superMode > 0:
                superMode -= 1

            tpil.clear()
            for r in range(ROWS):
                for c in range(COLS):
                    if maze[r][c] == 1:
                        tpil.draw.rectangle([c * T, r * T, c * T + T - 1, r * T + T - 1], outline=0, fill=None)
            for d in dots:
                tpil.rect([d[0] * T + 3, d[1] * T + 3], [d[0] * T + 4, d[1] * T + 4])
            for g in ghosts:
                tpil.rect([g["x"] * T + 1, g["y"] * T + 1], [g["x"] * T + 6, g["y"] * T + 6])
            cx = pacX * T
            cy = pacY * T
            tpil.draw.ellipse([cx + 1, cy + 1, cx + 6, cy + 6], fill=0)
            if moveDir == (1, 0):
                tpil.draw.rectangle([cx + 4, cy + 2, cx + 6, cy + 5], fill=1)
            elif moveDir == (-1, 0):
                tpil.draw.rectangle([cx + 1, cy + 2, cx + 3, cy + 5], fill=1)
            elif moveDir == (0, -1):
                tpil.draw.rectangle([cx + 2, cy + 1, cx + 5, cy + 3], fill=1)
            elif moveDir == (0, 1):
                tpil.draw.rectangle([cx + 2, cy + 4, cx + 5, cy + 6], fill=1)
            tpil.text([2, 2], "S:{}".format(score), fontSize=16)
            tpil.show()
            frame += 1
