import threading
import time
from core.badusb.badusb import BadUSB

class KeyReflectionSocket():
    """
    a socket that uses USB key reflection (capslock, scroll-lock, numlock) to transfer data
    """

    def __init__(self, commtype="ddr", createUSB=True) -> None:
        self.commtype = commtype

        if createUSB == True:
            self.usb = BadUSB()
            self.usbWasCreated = True
        else:
            self.usb = createUSB
            self.usbWasCreated = False

        self.usb.keyReflectListeners.append(self.__update__)
        self.mode = 0 # 0 for recieve, 1 for transmit
        
        self.recvBuffer = []
        self.byteBuffer = b""
        self.strBitBuffer = ""
        self.lastActivity = 0

        self.bufferFilled = False
        self.destroy = False

        self.encoded = {
            "ra": (self.usb.keys['null']*8).encode(),
            "caps": (self.usb.keys["null"]*2+chr(0x39)+self.usb.keys["null"]*5).encode(),
            "scrl": (self.usb.keys["null"]*2+chr(0x47)+self.usb.keys["null"]*5).encode(),
            "numl": (self.usb.keys["null"]*2+chr(0x53)+self.usb.keys["null"]*5).encode(),
            "kana": (self.usb.keys["null"]*2+chr(0x88)+self.usb.keys["null"]*5).encode(),
            "cmps": (self.usb.keys["null"]*2+chr(0x65)+self.usb.keys["null"]*5).encode(),
        }

        self.bufThread = threading.Thread(target=self.__bufferThread__, daemon=True)
        self.bufThread.start()

    def __bufferThread__(self):
        while True:
            if self.destroy: return
            ctime = time.time()

            if ctime-self.lastActivity >= 1 and len(self.byteBuffer) > 0:
                print("[+] sent {} bytes to buffer".format(len(self.byteBuffer)))

                self.recvBuffer.append(self.byteBuffer)
                self.byteBuffer = b""

            time.sleep(0.5)

    def __update__(self, caps, num, scroll, kana, compose):

        self.lastActivity = time.time()
        if self.mode == 0: # rx mode
            if self.commtype == "ddr": # new type, custom payload
                # needs 4 clock cycles to transmit 1 byte
                clock = caps
                tx1 = num
                tx2 = scroll
                
                if clock:
                    for bit in [tx1,tx2]:
                        if bit:
                            self.strBitBuffer += "1"
                        else:
                            self.strBitBuffer += "0"

            elif self.commtype == "sdr": # hak5 payload, 1 bit transmit, 1 bit rdy, 1 bit clk
                # needs 8 clock cycles to transmit 1 byte
                clock = scroll
                tx1 = caps
                rdy = num

                if clock:
                    for bit in [tx1]:
                        if bit:
                            self.strBitBuffer += "1"
                        else:
                            self.strBitBuffer += "0"

            if len(self.strBitBuffer) == 8:
                self.byteBuffer += int(self.strBitBuffer, 2).to_bytes(1, byteorder='big')
                self.strBitBuffer = ""
                print(self.byteBuffer)
                    
    def setKey(self, key:str, target:bool, flush=True, ra=True):
        value = None

        if key == "CAPSLOCK":
            value = self.usb.capsLock
        elif key == "SCROLLLOCK":
            value = self.usb.scrollLock
        elif key == "NUMLOCK":
            value = self.usb.numLock
        elif key == "COMPOSE":
            value = self.usb.compose
        elif key == "KANA":
            value = self.usb.kana

        if value != target:
            if key == "CAPSLOCK":
                self.usb.keyboard.write(self.encoded["caps"])
            if key == "SCROLLLOCK":
                self.usb.keyboard.write(self.encoded["scrl"])
            if key == "NUMLOCK":
                self.usb.keyboard.write(self.encoded["numl"])
            if key == "KANA":
                self.usb.keyboard.write(self.encoded["kana"])
            if key == "COMPOSE":
                self.usb.keyboard.write(self.encoded["cmps"])

        #if ra: self.usb.releaseAll()
        if ra: self.usb.keyboard.write(self.encoded["ra"])

    def destroy(self):
        self.usb.keyReflectListeners.clear()
        self.destroy = True

        if self.usbWasCreated:
            self.usb.close()

        self.bufThread.join()

        return True

    def recv(self):
        if not self.usb.capsLock and not self.usb.scrollLock and not self.usb.numLock:
            return self.recvBuffer.pop(0)
        
    def isDone(self):
        return not self.usb.capsLock and not self.usb.scrollLock and not self.usb.numLock # all off

    def send(self, transmitBytes:bytes, clockDelay=0, bitDelay=0.001):
        # tx1 = numlock = first bit
        # tx2 = scroll  = second bit
        # clock = caps


        self.mode = 1 # transmit mode - make sure our read thread doesn't get this
        for byte in transmitBytes:
            # set data first
            binary = format(byte, '08b')
            
            while len(binary) != 0:
                f2b = binary[:2] # get first two bits
                binary = binary[2:] # remove first two bits

                # turn str bits to bool
                bitOne = (f2b[0] == "1")
                bitTwo = (f2b[1] == "1")

                # set clock low
                self.setKey("CAPSLOCK", False, flush=False)

                # set bits
                self.setKey("NUMLOCK",    bitOne, flush=False)
                self.setKey("SCROLLLOCK", bitTwo, flush=False)

                # wait for bits to be sent
                time.sleep(clockDelay)

                # set clock high
                self.setKey("CAPSLOCK", True, flush=True)

                # wait for clock to be sent, and target to read
                time.sleep(bitDelay)

        
        self.setKey("CAPSLOCK", False) # reset
        self.setKey("NUMLOCK", False) # reset
        self.setKey("SCROLLLOCK", False) # reset

        self.usb.releaseAll() # this is vital

        self.mode = 0 # back to rx mode