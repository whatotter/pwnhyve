import gpiozero as gpioz
from core.plugin import BasePwnhyvePlugin 
import plugins.IO._pins as pinMGR
import spidev

# https://wiki.flashrom.org/RaspberryPi

def createSPIDevice(tpil):

    c = tpil.gui.screenConsole(tpil)
    c.text = '\n'.join([
        "CSn  -> Pin 5",
        "SCLK -> Pin 4",
        "MISO -> Pin 6",
        "MOSI -> Pin 7",
        "... waiting for user"
    ])
    c.forceUpdate()

    if tpil.waitForKey() == "left": return None

    device = spidev.SpiDev(0,2)

    return device

class PWNDumper(BasePwnhyvePlugin):
    def SPI_Flash_Dumper(tpil):
        device = createSPIDevice(tpil)

        if device == None:
            return
        
        ident = device.xfer2([0x9F] + [0x00]*3) # read ID

        print(f"Manufacturer ID: {ident}")