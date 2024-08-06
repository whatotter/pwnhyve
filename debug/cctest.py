import time
import core.cc1101.ccrf as rf
import core.cc1101.binary as binTranslate
from cc1101.addresses import (
    StrobeAddress,
    StatusRegisterAddress
)

a = rf.pCC1101()

def transtest(a:rf.pCC1101, bits):

    time.sleep(2.5)

    a.setupRawTransmission()

    time.sleep(2.5)

    print("BINGOBNH")

    a.rawTransmit2(bits, delayms=1)

def recvtest(a):
    a.setupRawRecieve()


    time.sleep(0.5)

    startedReceiving = False
    bits = []

    while True:
        try:
            print('start..')
            bits = a.rawRecv(1000)
            time.sleep(1)
        except:
            break

    print("done")

    return bits



transtest(a, recvtest(a))

a.close()