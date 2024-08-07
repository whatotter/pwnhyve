# /*****************************************************************************
# * | File        :	  config.py
# * | Author      :   Waveshare team
# * | Function    :   Hardware underlying interface,for Raspberry pi
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2020-06-17
# * | Info        :   
# ******************************************************************************/
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


import time
from smbus import SMBus
import spidev
import ctypes
import RPi.GPIO as GPIO
import pytoml as toml

# Pin definition
RST_PIN        = 25
CS_PIN         = 8
DC_PIN         = 24

#GPIO define
KEY_UP_PIN     = 31 
KEY_DOWN_PIN   = 35
KEY_LEFT_PIN   = 29
KEY_RIGHT_PIN  = 37
KEY_PRESS_PIN  = 33

KEY1_PIN       = 40
KEY2_PIN       = 38
KEY3_PIN       = 36

cfg = toml.loads(open("./config.toml").read())

Device_SPI = cfg["driver_options"]["spi"]
Device_I2C = not cfg["driver_options"]["spi"]

class RaspberryPi:
    def __init__(self,spi=None,spi_freq=40000000,rst = 27,dc = 25,bl = 18,bl_freq=1000,i2c=None):
        self.INPUT = False
        self.OUTPUT = True
        
        if(Device_SPI == 1):
            print("{+} display is in SPI mode")
            self.Device = Device_SPI
            self.spi = spidev.SpiDev(0, 0)
            self.GPIO_DC_PIN = self.gpio_mode(DC_PIN,self.OUTPUT)
        else :
            print("{+} display is in I2C mode")
            self.Device = Device_I2C
            self.address = 0x3c
            self.bus = SMBus(1)
        
        self.GPIO_RST_PIN = self.gpio_mode(RST_PIN,self.OUTPUT)




    def delay_ms(self,delaytime):
        time.sleep(delaytime / 1000.0)

    def gpio_mode(self,Pin,Mode,pull_up = None,active_state = True):
        if Mode:
            GPIO.setup(Pin, GPIO.OUT)
        else:
            GPIO.setup(Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        return Pin


    def gpio_pwm(self,Pin):
        return PWMOutputDevice(Pin,frequency = 10000)

    def set_pwm_Duty_cycle(self,Pin,value):
        Pin.value = value

    def digital_write(self, Pin, value):
        GPIO.output(Pin, value)

    def digital_read(self, Pin):
        return GPIO.input(Pin)

    def spi_writebyte(self,data):
        self.spi.writebytes([data[0]])

    def i2c_writebyte(self,reg, value):
        self.bus.write_byte_data(self.address, reg, value)
    
    def module_init(self): 
        self.digital_write(self.GPIO_RST_PIN,False)
        if(self.Device == Device_SPI):
            self.spi.max_speed_hz = 1000000
            self.spi.mode = 0b11  
            self.digital_write(self.GPIO_DC_PIN,False)
            #CS_PIN.off()
        return 0

    def module_exit(self):
        if(self.Device == Device_SPI):
            self.spi.close()
            self.digital_write(self.GPIO_RST_PIN,False)
            self.digital_write(self.GPIO_DC_PIN,False)
        else :
            self.bus.close()

### END OF FILE ###
