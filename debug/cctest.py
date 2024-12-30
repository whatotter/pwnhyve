import time
import core.cc1101.ccrf as rf
import core.cc1101.binary as binTranslate

a = rf.pCC1101()

def transtest(a:rf.pCC1101, bits):

    #time.sleep(2.5)

    a.setupRawTransmission()

    time.sleep(1)

    #print("BINGOBNH")

    #print(bits)

    a.rawTransmit2(bits, delayms=100)
    #a.oldRawTransmit2(bits, delayms=100)

def recvtest(a):
    a.setupRawRecieve()


    time.sleep(1)

    startedReceiving = False
    bits = []

    print('start..')
    bits = a.recvSamples(1000)
    time.sleep(1)

    print("done")

    return ([0] * 8 + [1] * 8) * 8

def text_to_bits(text):
    # Convert each character to its ASCII value, then to binary
    bits = []
    for char in text:
        # Get the ASCII value, convert to binary, and pad with zeros to ensure 8 bits
        binary = format(ord(char), '08b')
        # Extend the bits list with the bits of the current character
        bits.extend(int(bit) for bit in binary)
    return bits

transtest(a, text_to_bits("otter was here!!!!")*32)