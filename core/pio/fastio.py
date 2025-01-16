import os
import subprocess

def hz2NS(hz):
    if hz <= 0:
        raise ValueError("frequency must be greater than 0hz")
    
    return (1 / hz) * 1e9

def bitToByte(bits:list):

    if type(bits) == str:
        bits = [int(x) for x in bits]

    # Ensure bits are in groups of 8
    if len(bits) % 8 != 0:
        print("The number of bits must be a multiple of 8. They are: {}. Simply adding padding for now..".format(len(bits)))

        while len(bits) % 8 != 0:
            bits.append(0)

    bytes_list = []
    
    # Iterate through the bits in chunks of 8
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]  # Get the next 8 bits
        byte_value = sum(b << (7 - j) for j, b in enumerate(byte))  # Convert to byte value
        bytes_list.append(byte_value)
    
    return b''.join([x.to_bytes(1) for x in bytes_list])

class FastIO:
    """
    USES RAW BCM2835 PINOUTS!!!
       
    +-----+---------+----------+---------+-----+ 
    | BCM |   Name  | Physical | Name    | BCM | 
    +-----+---------+----++----+---------+-----+
    |     |    3.3v |  1 || 2  | 5v      |     |
    |   2 |   SDA 1 |  3 || 4  | 5v      |     |
    |   3 |   SCL 1 |  5 || 6  | 0v      |     |
    |   4 | GPIO  7 |  7 || 8  | TxD     | 14  |
    |     |      0v |  9 || 10 | RxD     | 15  |
    |  17 | GPIO  0 | 11 || 12 | GPIO  1 | 18  |
    |  27 | GPIO  2 | 13 || 14 | 0v      |     |
    |  22 | GPIO  3 | 15 || 16 | GPIO  4 | 23  |
    |     |    3.3v | 17 || 18 | GPIO  5 | 24  |
    |  10 |    MOSI | 19 || 20 | 0v      |     |
    |   9 |    MISO | 21 || 22 | GPIO  6 | 25  |
    |  11 |    SCLK | 23 || 24 | CE0     | 8   |
    |     |      0v | 25 || 26 | CE1     | 7   |
    |   0 |   SDA 0 | 27 || 28 | SCL 0   | 1   |
    |   5 | GPIO 21 | 29 || 30 | 0v      |     |
    |   6 | GPIO 22 | 31 || 32 | GPIO 26 | 12  |
    |  13 | GPIO 23 | 33 || 34 | 0v      |     |
    |  19 | GPIO 24 | 35 || 36 | GPIO 27 | 16  |
    |  26 | GPIO 25 | 37 || 38 | GPIO 28 | 20  |
    |     |      0v | 39 || 40 | GPIO 29 | 21  |
    +-----+---------+----++----+---------+-----+
    """
    def __init__(self) -> None:
        self.delayNS = 0

        self._executable_ = "./core/pio/pio"
        self._process_ = None
        self.defaultArgs = {
            "samples": "-1",
            "file": "samples.bin",
            "pin": "-1",
            "mode": "rx",
            "sleep": "1000" # 1us, 1mhz
        }
        self.args = self.defaultArgs
        self.nice = -19

        pass

    def hz2NS(self, hz):
        if hz <= 0:
            raise ValueError("frequency must be greater than 0hz")
        
        return (1 / hz) * 1e9

    def flipperSend(self, pin, RAW_Data) -> None:
        """
        transmit bits to a pin, the flipper way
        """

        with open("flip.bin", "w") as f:
            f.write(RAW_Data)
            f.flush()

        self.args["mode"] = "txflp"
        self.args['file'] = 'flip.bin'
        self.args["pin"] = pin

        self.__launchProcess__()

        self._process_.wait()

        #os.remove("flip.bin")

    def calcBinFile(self, bits, filename = "fastio_tx.bin"):
        """
        turns bits into a bin file for later use
        """

        with open(filename, "wb") as f:
            f.write(
                bitToByte(
                    ''.join([str(x) for x in bits])
                )
            )
            f.flush()

        return filename

    def send(self, pin, bits, ns=1000):
        """
        transmit bits to a pin

        if `bits` is a list,   write it to a .bin file for the `pio` executable

        if `bits` is a string, open that as a path
        """

        self.args = self.defaultArgs

        if type(bits) == str:
            self.args["file"] = bits
        else:
            with open("fastio_tx.bin", "wb") as f:
                f.write(
                    bitToByte(
                        ''.join([str(x) for x in bits])
                    )
                )
                f.flush()
        
            self.args["file"] = "fastio_tx.bin"

        self.args["mode"] = "tx"
        self.args["pin"] = pin
        self.args["sleep"] = round(ns)

        self.__launchProcess__()
        
        self._process_.wait()


    def readSamples(self, pins:list|int, samples:int, output:str=None, bg:bool=False) -> list | subprocess.Popen:
        """
        Read X amount of samples.
        This function *is* blocking, if bg==False.
        """

        if type(pins) == int: pins = [pins]

        self.args["pin"] = pins
        self.args["samples"] = samples
        self.args["mode"] = "rx"
        
        if output != None:
            self.args["file"] = output
        else:
            self.args["file"] = 'samples'

        proc = self.__launchProcess__(bg=bg)

        if not bg: 
            proc.wait()
            if output == None: # output file was not set
                return [self.__parseBin__(x) for x in pins]
            else: # output file was set
                return [self.__parseBin__(x, binf=output) for x in pins]
        else:
            return proc
    
    def infread(self, pins:list|int, filename="infread") -> subprocess.Popen:
        """
        Read pin X till death (by self.close()).
        Non-blocking.
        """

        if type(pins) == int: pins = [pins]

        self.args["pin"] = pins
        self.args["samples"] = "-1"
        self.args["mode"] = "rx"
        self.args["file"] = filename

        return self.__launchProcess__()
        
    def close(self) -> list:
        """
        Close program, if there is one, running.

        Auto-guesses the pin parameter and binfile name for parsebin. Should (hopefully) always be successful in parsing the most recent binfile.
        """
        self._process_.send_signal(15)
        self._process_.wait()

        try:
            return [self.__parseBin__(pin, binf=self.args['file']) for pin in self.args["pin"].split(",")]
        except:
            return None
        
    def setHZ(self, hz):
        """
        set polling rate to X hz
        """

        self.args["sleep"] = int(hz2NS(hz)-500 if hz2NS(hz)-500 > 0 else 0)
        print("[+] set PIO sleep to {}ns".format(hz2NS(hz)-500))

    def setNS(self, ns):
        """
        set polling rate to X nanoseconds (min is ~500ns, overhead)
        """
        self.args["sleep"] = int(ns-500 if ns-500 > 0 else 0)
        print("[+] set PIO sleep to {}ns".format(ns))

    def __launchProcess__(self, bg=False) -> None:
        """
        launch pio program
        """

        cmd = [self._executable_] + self.__compileArgs__()

        if self.nice is not None:
            cmd = ["nice", "-n", "-20"] + cmd

        print("[+] {}".format(' '.join(cmd)))

        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        
        # process is started, reset args
        self.args = self.defaultArgs

        if bg == False: # running in blocking mode
            self._process_ = process # allow other functions to access

        return process

    def __compileArgs__(self) -> list:
        """
        compile args to one list for Popen
        """
        x = []

        for param,val in self.args.items():

            if type(val) == list:
                for item in val:
                    x.append("--"+param)
                    x.append(str(item))
            else:
                x.append("--"+param)
                x.append(str(val))

        return x
    
    def __parseBin__(self, pin, binf="samples", remove=False) -> str:
        """parse bin file to bits"""
        bits = []

        with open("{}-{}.bin".format(binf, pin), "rb") as f:
            byts = f.read()

        for byte in byts:
            bits += [int(x) for x in format(byte, '08b')]

        if remove:
            os.remove("{}-{}.bin".format(binf, pin))

        return bits
    
    def __readProcess__(self) -> None:
        """debug function"""
        while True:
            try:
                self._process_.stdout.read(1)
            except:
                raise

if __name__ == "__main__":
    io = FastIO()

    io.setHZ(2_000_000) # 2mhz
    bits = io.readSamples(18, 11221)
    print("{} bits".format(len(bits)))

    io.setNS(0)

    io.send(18, [1,0,0,1,0,0,1,1])

    #bits = [1,0,0,1,0,0,1,1]