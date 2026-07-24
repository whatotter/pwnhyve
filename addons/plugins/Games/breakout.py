import random
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def breakout(tpil:tinyPillow):
        paddleW, paddleH = 16, 4
        ballSize = 3
        paddleX = 56
        ballX, ballY = 64.0, 56.0
        ballDX = random.choice([-2, 2])
        ballDY = -2.0
        bricks = []
        score = 0
        lives = 3
        respawnTimer = 0

        for r in range(4):
            for c in range(12):
                if random.random() < 0.85:
                    bricks.append([c * 10 + 4, r * 6 + 4, 8, 4])

        while True:
            key = tpil.checkIfKey()
            if key == False:
                key = None

            if key == "left" and paddleX > 0:
                paddleX -= 4
            elif key == "right" and paddleX < 128 - paddleW:
                paddleX += 4

            if respawnTimer > 0:
                respawnTimer -= 1
                tpil.clear()
                for bx, by, bw, bh in bricks:
                    tpil.rect([bx, by], [bx + bw, by + bh])
                tpil.rect([paddleX, 60], [paddleX + paddleW, 60 + paddleH])
                tpil.rect([int(ballX), int(ballY)], [int(ballX) + ballSize, int(ballY) + ballSize])
                tpil.text([2, 2], "{} Lives: {}".format(score, lives), fontSize=16)
                tpil.show()
                continue

            ballX += ballDX
            ballY += ballDY

            if ballX <= 0 or ballX >= 128 - ballSize:
                ballDX = -ballDX
            if ballY <= 0:
                ballDY = -ballDY

            if ballDY > 0 and ballY + ballSize >= 60 and ballY < 60 + paddleH:
                if ballX + ballSize > paddleX and ballX < paddleX + paddleW:
                    ballDY = -ballDY
                    ballY = 60 - ballSize

            if ballY > 64:
                lives -= 1
                if lives == 0:
                    tpil.gui.toast("Game Over\nScore: {}".format(score), [10, 10], [118, 54])
                    return
                ballX, ballY = 64.0, 56.0
                paddleX = 56
                ballDX = random.choice([-2, 2])
                ballDY = -2.0
                respawnTimer = 30
                continue

            for b in bricks[:]:
                bx, by, bw, bh = b
                if bx < ballX + ballSize and bx + bw > ballX and by < ballY + ballSize and by + bh > ballY:
                    bricks.remove(b)
                    score += 1
                    ballDY = -ballDY
                    break

            if not bricks:
                tpil.gui.toast("You Win!\nScore: {}".format(score), [10, 10], [118, 54])
                return

            tpil.clear()
            for bx, by, bw, bh in bricks:
                tpil.rect([bx, by], [bx + bw, by + bh])
            tpil.rect([paddleX, 60], [paddleX + paddleW, 60 + paddleH])
            tpil.rect([int(ballX), int(ballY)], [int(ballX) + ballSize, int(ballY) + ballSize])
            tpil.text([2, 2], "{} Lives: {}".format(score, lives), fontSize=16)
            tpil.show()
