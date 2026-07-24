import random
import time
from core.plugin import BasePwnhyvePlugin
from core.pil_simplify import tinyPillow

class Plugin(BasePwnhyvePlugin):
    def galaga(tpil:tinyPillow):
        playerX = 56
        playerW, playerH = 8, 6
        bullets = []
        enemyBullets = []
        enemies = []
        score = 0
        lives = 3
        frame = 0
        enemyDir = 1
        wave = 0
        diving = []
        diveCooldown = 0
        spawnDelay = 0

        def spawnWave():
            nonlocal wave
            wave += 1
            cols = 6 + min(wave, 4)
            for c in range(cols):
                enemies.append([20 + c * 14, 8, False])

        spawnWave()

        while True:
            key = tpil.checkIfKey()
            if key == False:
                key = None

            if key == "left" and playerX > 0:
                playerX -= 3
            elif key == "right" and playerX < 128 - playerW:
                playerX += 3
            elif key == "press" or key == "up":
                if not bullets:
                    bullets.append([playerX + playerW // 2, 56])

            for b in bullets[:]:
                b[1] -= 3
                if b[1] < 0:
                    bullets.remove(b)

            for eb in enemyBullets[:]:
                eb[1] += 2
                if eb[1] > 64:
                    enemyBullets.remove(eb)

            if frame % 30 == 0 and enemies:
                idx = random.randint(0, len(enemies) - 1)
                if not enemies[idx][2]:
                    diving.append(enemies[idx])
                    enemies[idx][2] = True

            for e in diving[:]:
                e[1] += 2
                if e[1] > 56:
                    diving.remove(e)
                    e[1] = 8
                    e[2] = False
                if random.random() < 0.02:
                    enemyBullets.append([e[0] + 4, e[1] + 6])

            for e in enemies:
                if not e[2]:
                    e[0] += enemyDir
            if enemies:
                xs = [e[0] for e in enemies if not e[2]]
                if xs:
                    if min(xs) < 2:
                        enemyDir = 1
                    elif max(xs) > 118:
                        enemyDir = -1

            for b in bullets[:]:
                for e in enemies[:]:
                    if e[0] < b[0] < e[0] + 10 and e[1] < b[1] < e[1] + 6:
                        enemies.remove(e)
                        if e in diving:
                            diving.remove(e)
                        bullets.remove(b)
                        score += 1
                        break
                if b in bullets:
                    for e in diving[:]:
                        if e[0] < b[0] < e[0] + 10 and e[1] < b[1] < e[1] + 6:
                            diving.remove(e)
                            bullets.remove(b)
                            score += 1
                            break

            for eb in enemyBullets[:]:
                if playerX < eb[0] < playerX + playerW and 56 < eb[1] < 62:
                    lives -= 1
                    enemyBullets.remove(eb)
                    if lives == 0:
                        tpil.gui.toast("Game Over\nScore: {}".format(score), [10, 10], [118, 54])
                        return
                    playerX = 56
                    time.sleep(0.5)

            if not enemies and not diving:
                spawnDelay += 1
                if spawnDelay > 30:
                    spawnDelay = 0
                    spawnWave()

            tpil.clear()
            for e in enemies:
                tpil.rect([e[0], e[1]], [e[0] + 8, e[1] + 5])
            for e in diving:
                tpil.rect([e[0], e[1]], [e[0] + 8, e[1] + 5])
            for b in bullets:
                tpil.rect([b[0], b[1]], [b[0] + 1, b[1] + 3])
            for eb in enemyBullets:
                tpil.rect([eb[0], eb[1]], [eb[0] + 1, eb[1] + 3])
            tpil.rect([playerX, 56], [playerX + playerW, 56 + playerH])
            tpil.text([2, 2], "{} Lives: {}".format(score, lives), fontSize=16)
            tpil.show()
            frame += 1
