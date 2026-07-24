import random
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def pong(tpil:tinyPillow):
        paddleW, paddleH = 4, 12
        ballSize = 3
        playerY = 26
        aiY = 26
        ballX, ballY = 64.0, 32.0
        ballDX = random.choice([-2, 2])
        ballDY = random.choice([-2, 2])
        playerScore = 0
        aiScore = 0

        while True:
            key = tpil.checkIfKey()
            if key == False:
                key = None

            if key == "up" and playerY > 0:
                playerY -= 3
            elif key == "down" and playerY < 52:
                playerY += 3

            aiSpeed = min(2 + playerScore, 6)
            if aiY + 6 < ballY:
                aiY += aiSpeed
            elif aiY + 6 > ballY:
                aiY -= aiSpeed

            aiY = max(0, min(52, aiY))
            ballX += ballDX
            ballY += ballDY

            if ballY <= 0 or ballY >= 61:
                ballDY = -ballDY

            if ballX <= paddleW and playerY <= ballY <= playerY + paddleH:
                ballDX = -ballDX
                ballX = paddleW + 1

            if ballX >= 124 - paddleW and aiY <= ballY <= aiY + paddleH:
                ballDX = -ballDX
                ballX = 124 - paddleW - 1

            if ballX < 0:
                aiScore += 1
                ballX, ballY = 64.0, 32.0
                ballDX = random.choice([-2, 2])
                ballDY = random.choice([-2, 2])
            elif ballX > 128:
                playerScore += 1
                ballX, ballY = 64.0, 32.0
                ballDX = random.choice([-2, 2])
                ballDY = random.choice([-2, 2])

            if aiScore >= 5 or playerScore >= 5:
                tpil.gui.toast("Game Over\n{} wins".format("You" if playerScore > aiScore else "AI"), [10, 10], [118, 54])
                return

            tpil.clear()
            tpil.rect([0, playerY], [paddleW, playerY + paddleH])
            tpil.rect([124, aiY], [128, aiY + paddleH])
            tpil.rect([int(ballX), int(ballY)], [int(ballX) + ballSize, int(ballY) + ballSize])
            tpil.rect([63, 0], [64, 64])
            tpil.text([2, 2], str(playerScore), fontSize=16)
            tpil.text([116, 2], str(aiScore), fontSize=16)
            tpil.show()
