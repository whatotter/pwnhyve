import sys
import gpiozero as gpioz
import time

GDO2 = 22
cycles = 10*10*10*10*10

xyz = 0
compare = 100
rcTime = None
startTime = None

pin = gpioz.DigitalInputDevice(GDO2)

print('')

for x in range(cycles):
    startTime = time.time_ns()

    a = pin.value

    rcTime = time.time_ns() - startTime
    
    if xyz == compare:
        xyz = 0
        print("input i/o time: {}ns".format(rcTime))

    xyz += 1