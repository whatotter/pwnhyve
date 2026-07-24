import random
import time
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def tetris(tpil:tinyPillow):
        COLS, ROWS = 8, 16
        BS = 6
        OX = (128 - ROWS * BS) // 2
        OY = (64 - COLS * BS) // 2

        def tx(r, c):
            return OX + (ROWS - 1 - r) * BS, OY + c * BS

        SHAPES = [
            [[1,1,1,1]],
            [[1,1],[1,1]],
            [[1,0],[1,0],[1,1]],
            [[0,1],[0,1],[1,1]],
            [[1,1,0],[0,1,1]],
            [[0,1,1],[1,1,0]],
            [[1,1,1],[0,1,0]],
        ]

        board = [[0]*COLS for _ in range(ROWS)]
        current = None
        cr = cc = 0
        score = 0
        fallTimer = 0
        fallInterval = 0.4

        def newPiece():
            nonlocal current, cr, cc
            current = random.choice(SHAPES)
            cr = 0
            cc = COLS // 2 - len(current[0]) // 2

        def collide(shape, r, c):
            for sr, row in enumerate(shape):
                for sc, v in enumerate(row):
                    if v:
                        nr, nc = r + sr, c + sc
                        if nr < 0 or nr >= ROWS or nc < 0 or nc >= COLS:
                            return True
                        if board[nr][nc]:
                            return True
            return False

        def lock():
            nonlocal score, current, cr, cc
            for sr, row in enumerate(current):
                for sc, v in enumerate(row):
                    if v:
                        board[cr + sr][cc + sc] = 1
            cleared = 0
            for r in range(ROWS):
                if all(board[r]):
                    board.pop(r)
                    board.insert(0, [0]*COLS)
                    cleared += 1
            score += cleared * 10
            newPiece()
            if collide(current, cr, cc):
                tpil.gui.toast("Tetris\nScore: {}".format(score), [10, 10], [118, 54])
                return True
            return False

        newPiece()
        lastTime = time.time()

        while True:
            now = time.time()
            dt = now - lastTime
            lastTime = now
            fallTimer += dt

            key = tpil.getKey(debounce=True)
            if key == False:
                key = None

            if key == "up":
                if not collide(current, cr, cc - 1):
                    cc -= 1
            elif key == "down":
                if not collide(current, cr, cc + 1):
                    cc += 1
            elif key == "left":
                if not collide(current, cr + 1, cc):
                    cr += 1
            elif key == "right":
                rotated = list(zip(*current[::-1]))
                if not collide(rotated, cr, cc):
                    current = [list(r) for r in rotated]

            if fallTimer >= fallInterval:
                fallTimer = 0
                if not collide(current, cr + 1, cc):
                    cr += 1
                else:
                    if lock():
                        return

            tpil.clear()

            x0, y0 = tx(0, 0)
            x1, y1 = tx(ROWS - 1, COLS - 1)
            xl = min(x0, x1) - 1
            xr = max(x0, x1) + BS
            yt = min(y0, y1) - 1
            yb = max(y0, y1) + BS
            tpil.rect([xl, yt], [xr, yb])
            tpil.rect([xl + 1, yt + 1], [xr - 1, yb - 1], color="BLACK")

            for r in range(ROWS):
                for c in range(COLS):
                    if board[r][c]:
                        x, y = tx(r, c)
                        tpil.rect([x, y], [x + BS - 1, y + BS - 1])

            if current:
                for sr, row in enumerate(current):
                    for sc, v in enumerate(row):
                        if v:
                            x, y = tx(cr + sr, cc + sc)
                            tpil.rect([x, y], [x + BS - 1, y + BS - 1])

            tpil.text([2, 2], str(score), fontSize=16)
            tpil.show()
            time.sleep(0.016)
