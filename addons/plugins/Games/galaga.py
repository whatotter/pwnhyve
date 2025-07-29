import random
import time
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def galaga(tpil:tinyPillow):
        
        playerPos = 16
        enemiesFiring = 0
        playerFiring = False
        died = False
        waitSpawnFrames = 0
        maxEnemiesShooting = 1
        enemyHeight = 8
        score = 0
        enemyPositions = []
        formations = (
            [
                [84, 16, 0], [84, 32, 0], [84, 48, 0]
            ],
            [
                [100, 16, 0], [120, 24, 0], [100, 32, 0], [120, 40, 0], [100, 48, 0]
            ],
            [
                [96, 16+4, 0], [96, 36+4, 0], [80, 4+4, 0], [80, 48+4, 0], [112, 26+4, 0]
            ],
        )


        while True:

            # TODO: figure out a better way of doing this
            keyInputTime = time.time_ns() // 1_000_000
            key = tpil.waitWhileChkKey(0.1)
            keyOutputTime = time.time_ns() // 1_000_000

            if 100 > keyOutputTime - keyInputTime:
                timeMS = (keyOutputTime - keyInputTime) / 1000
                if timeMS >= 0.1:
                    pass
                else:
                    timeRemaining = 0.1 - timeMS
                    time.sleep(timeRemaining)

            if not died:
                if key == "down":
                    playerPos += 3
                elif key == "up":
                    playerPos -= 3
                elif key == "press" or key == "right":
                    playerFiring = 2

            tpil.clear()

            playerFiringY = 0
            enemyFiringY = 0
            if playerFiring:
                tpil.rect([0, playerPos+5], [200, playerPos+5])
                playerFiringY = playerPos+5
                playerFiring -= 1

            enemiesFiring = 0
            for enemy in enemyPositions.copy():
                yOffset = 0
                shootFrame = enemy[2]

                if shootFrame > 0:
                    enemiesFiring += 1

                if shootFrame > 0 and 4 >= shootFrame: # if we're out of the animation
                    tpil.rect([0, enemy[1]-1], [(enemy[0]/4) * shootFrame, enemy[1]+1])
                    enemyFiringY = enemy[1]
                    enemy[2] -= 1

                if shootFrame > 0 and shootFrame > 4: # animation
                    yOffset = 1 if shootFrame % 2 == 0 else -1
                    tpil.rect([0, enemy[1]], [enemy[0], enemy[1]])
                    enemy[2] -= 1
                    
                if enemy[1]-4 < playerFiringY and enemy[1]+4 > playerFiringY:
                    enemyPositions.remove(enemy)
                    score += 1
                    if score % 10 == 0:
                        maxEnemiesShooting += 1
                        if enemyHeight != 2:
                            enemyHeight -= 2

                splitSz = enemyHeight / 2
                tpil.rect([enemy[0]-splitSz, enemy[1]+yOffset-splitSz], [enemy[0]+splitSz, enemy[1]+splitSz + yOffset])

            for enemy in enemyPositions.copy(): # manage shooting
                if random.randint(1,6) == 2 and shootFrame == 0 and enemiesFiring <= maxEnemiesShooting and waitSpawnFrames == 16:
                    enemy[2] = 16
                    enemiesFiring += 1
                    break

            # player managemnet
            if enemyFiringY > playerPos and playerPos+10 > enemyFiringY:
                died = True
                pass

            print("Enemies left: {}".format(len(enemyPositions)))
            print("Max enemies shooting: {}".format(maxEnemiesShooting))
            if len(enemyPositions) == 0:
                if waitSpawnFrames == 4:
                    enemyPositions = random.choice(formations).copy()
                    for enemy in enemyPositions:
                        enemy[2] = 0
                elif waitSpawnFrames >= 4:
                    waitSpawnFrames = 0
            
            if waitSpawnFrames != 16:
                waitSpawnFrames += 1

            tpil.rect([11, playerPos], [12, playerPos+10])

            tpil.text([112, 4], "{}".format(score), fontSize=16)

            tpil.show()

            if died:
                time.sleep(2.5)
                return