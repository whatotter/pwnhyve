import gpiozero as gpioz
from core.plugin import BasePwnhyvePlugin 
import plugins.IO._pins as pinMGR

def createPWM(tpil, pin):

    slider = tpil.gui.slider(tpil, "PWM Hz", minimum=1, maximum=1000)
    hz = slider.draw()

    clearPin(pin) # clear pin before changing to PWM
    pinObject = gpioz.PWMOutputDevice(pin, frequency=hz)
    pinObject.value = 0.5

    return pinObject

def createOut(tpil, pin):
    
    pinObject = gpioz.OutputDevice(pin)

    return pinObject

def createServo(tpil, pin):
    
    pinObject = gpioz.Servo(pin)

    return pinObject

def clearPin(pin):
    if pin in pinObjects: pinObjects[pin].close()

pinModeStrings = {
    "PWM": createPWM,
    "Output": createOut
}

class PWNPlayground(BasePwnhyvePlugin):
    def Playground(tpil):
        global pinObjects
        pinObjects = {}
        pinModeStrings = {}
        pinModes = {}
        modeIndex = -1

        while True:
            modeIndex = -1
            pin = pinMGR.requestPin(tpil, list(pinModeStrings), pinModeStrings, minimize=True)

            while True:
                mode, modeIndex = tpil.gui.menu([
                    "PWM",
                    "Output",
                    "Servo",
                    "Buzzer",
                    "Distance Sensor"
                ], index=modeIndex)

                pinName = pinMGR.pinLookup(pin)

                if mode == "PWM":
                    #  if pin was not set, or pin is not in PWM mode already
                    if pin not in pinObjects or pinModes.get(pinName) != "PWM":
                        pinObjects[pin] = createPWM(tpil, pin) # then make it pwm
                    else: # if already in PWM mode
                        # then edit the config for pwm mode
                        todo = tpil.gui.menu(["Edit Frequency", "Edit Value", "Pulse"])
                        if todo == "Edit Frequency":
                            pinObjects[pin] = createPWM(tpil, pin)
                        elif todo == "Edit Value":
                            pinObjects[pin].value = tpil.gui.slider(tpil, "PWM Value", 
                                                                    minimum=0, maximum=1, 
                                                                    step=0.01, bigstep=0.1,
                                                                    ndigits=2).draw()
                        elif todo == "Pulse":
                            pinObjects[pin].pulse()

                    pinModeStrings[pinName] = "({}hz / {})".format(pinObjects[pin].frequency, pinObjects[pin].value)
                    pinModes[pinName] = "PWM"

                elif mode == "Output":

                    if pin not in pinObjects or pinModes.get(pinName) != ">":
                        pinObjects[pin] = createOut(tpil, pin)
                    else:
                        pinObjects[pin].value = not pinObjects[pin].value

                    pinModeStrings[pinName] = "({})".format('ON' if pinObjects[pin].value else 'OFF')
                    pinModes[pinName] = ">"

                elif mode == "Servo":
                    if pin not in pinObjects or pinModes.get(pinName) != "Servo":
                        pinObjects[pin] = createServo(tpil, pin)
                    else:
                        pinObjects[pin].value = tpil.gui.slider(tpil, "Servo Value", 
                                                                    minimum=-1, maximum=1, 
                                                                    step=0.01, bigstep=0.1,
                                                                    ndigits=2).draw()

                    pinModeStrings[pinName] = "(Servo {})".format(pinObjects[pin].value)
                    pinModes[pinName] = "Servo"

                elif mode == None:
                    break

                # flash
                tpil.clear()
                tpil.show()
            


