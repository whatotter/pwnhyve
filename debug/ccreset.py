
import time
from RPi import GPIO

csn = 12

GPIO.setmode(GPIO.BOARD)
GPIO.setup(csn, GPIO.IN)

time.sleep(2.5)

GPIO.setup(csn, GPIO.OUT)
GPIO.output(csn, 1)
time.sleep(0.5)
GPIO.cleanup()

print('done')