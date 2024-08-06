import sys
from RPi import GPIO
import time

GDO2 = 22
cycles = 10*10*10*10*10

xyz = 0
compare = 100
rcTime = None
startTime = None

GPIO.setmode(GPIO.BOARD)
GPIO.setup(GDO2, GPIO.IN)

print('')

for x in range(cycles):
    startTime = time.time_ns()

    a = GPIO.input(GDO2)

    rcTime = time.time_ns() - startTime
    
    if xyz == compare:
        xyz = 0
        print("input i/o time: {}ns".format(rcTime))

    xyz += 1