import random
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def dino(tpil:tinyPillow):
        groundY = 56
        dinoX = 20
        dinoW, dinoH = 4, 8
        dinoY = groundY - dinoH
        gravity = 1.2
        jumpVel = -9
        velocity = 0
        isJumping = False
        obstacles = []
        score = 0
        frame = 0
        minGap = 40

        while True:
            key = tpil.checkIfKey()

            if (key == "up" or key == "press") and not isJumping:
                velocity = jumpVel
                isJumping = True

            velocity += gravity
            dinoY += velocity
            if dinoY >= groundY - dinoH:
                dinoY = groundY - dinoH
                isJumping = False
                velocity = 0

            baseSpeed = 3 + score // 10

            if frame % 2 == 0:
                if not obstacles or obstacles[-1][0] < 128 - minGap - score:
                    if random.randint(1, max(2, 3 - score // 15)) == 1:
                        h = random.choice([6, 8, 10])
                        obstacles.append([128, groundY - h, 4, h])
                for obs in obstacles[:]:
                    obs[0] -= baseSpeed
                    if obs[0] < -10:
                        obstacles.remove(obs)
                        score += 1

            cx1, cy1 = dinoX + 1, dinoY + 1
            cx2, cy2 = dinoX + dinoW - 1, dinoY + dinoH - 1
            for ox, oy, ow, oh in obstacles:
                if cx1 < ox + ow and cx2 > ox and cy1 < oy + oh and cy2 > oy:
                    tpil.gui.toast("Game Over\nScore: {}".format(score), [10, 10], [118, 54])
                    return

            tpil.clear()
            tpil.rect([0, groundY], [128, groundY + 1])
            tpil.rect([dinoX, dinoY], [dinoX + dinoW, dinoY + dinoH])

            for ox, oy, ow, oh in obstacles:
                tpil.rect([ox, oy], [ox + ow, oy + oh])

            tpil.text([2, 2], "Score: {}".format(score), fontSize=16)
            tpil.show()
            frame += 1
