from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def connect4(tpil:tinyPillow):
        COLS, ROWS = 7, 6
        BS = 10
        OX = (128 - COLS * BS) // 2
        OY = (64 - ROWS * BS) // 2
        board = [[0]*COLS for _ in range(ROWS)]
        player = 1
        cursor = 3
        gameOver = False

        def drop(col):
            nonlocal gameOver, player
            for r in range(ROWS-1, -1, -1):
                if board[r][col] == 0:
                    board[r][col] = player
                    if checkWin(r, col, player):
                        gameOver = True
                        return True
                    player = 3 - player
                    return True
            return False

        def checkWin(r, c, p):
            for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
                count = 1
                for d in (1, -1):
                    nr, nc = r + dr*d, c + dc*d
                    while 0 <= nr < ROWS and 0 <= nc < COLS and board[nr][nc] == p:
                        count += 1
                        nr += dr*d
                        nc += dc*d
                if count >= 4:
                    return True
            return False

        while not gameOver:
            key = tpil.waitWhileChkKey(0.1)

            if key == "left" and cursor > 0:
                cursor -= 1
            elif key == "right" and cursor < COLS - 1:
                cursor += 1
            elif key == "press":
                drop(cursor)
            elif key == "3":
                return

            tpil.clear()
            for r in range(ROWS):
                for c in range(COLS):
                    x = OX + c * BS
                    y = OY + r * BS
                    tpil.draw.rectangle([x, y, x + BS - 1, y + BS - 1], fill=255, outline=0)
                    if board[r][c] == 1:
                        tpil.draw.ellipse([x + 1, y + 1, x + BS - 2, y + BS - 2], fill=0)
                    elif board[r][c] == 2:
                        tpil.draw.line([x + 2, y + 2, x + BS - 3, y + BS - 3], fill=0)
                        tpil.draw.line([x + BS - 3, y + 2, x + 2, y + BS - 3], fill=0)

            cx = OX + cursor * BS
            tpil.draw.rectangle([cx + 1, OY - 3, cx + BS - 2, OY - 1], fill=0)
            tpil.text([2, 2], "P{}'s turn".format(player), fontSize=16)
            tpil.show()

        tpil.gui.toast("Player {} Wins!".format(player), [10, 10], [118, 54])
