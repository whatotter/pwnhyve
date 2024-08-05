import os
import subprocess
import sys
from RPi import GPIO
import time

GDO2 = 22
cycles = 10*10*10*10

xyz = 0
compare = 100
rcTime = None
startTime = None

gpioDir = "/sys/class/gpio/gpio{}".format(GDO2)
subprocess.getoutput("echo {} > /sys/class/gpio/export".format(GDO2))
subprocess.getoutput("echo in > {}/direction".format(gpioDir))

iofile = open("{}/value".format(gpioDir), "rb")

print('')

for x in range(cycles):
    startTime = time.time_ns()

    a = iofile.read(1)

    rcTime = time.time_ns() - startTime
    
    if xyz == compare:
        xyz = 0
        print("input i/o time: {}ns".format(rcTime))

    xyz += 1