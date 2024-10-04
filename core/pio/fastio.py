import os
import subprocess

def hz2NS(hz):
    if hz <= 0:
        raise ValueError("frequency must be greater than 0hz")
    
    return (1 / hz) * 1e9

def bitToByte(bits):
    byte_value = int(bits, 2)  # Convert to integer
    return bytes([byte_value])  # Convert to byte object

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

        self._executable_ = "./pio"
        self._process_ = None
        self.defaultArgs = {
            "samples": "-1",
            "file": "samples.bin",
            "pin": "-1",
            "mode": "rx",
            "sleep": "1000" # 1us, 1mhz
        }
        self.args = self.defaultArgs

        pass

    def flipperSend(self, pin, RAW_Data) -> None:
        """
        transmit bits to a pin, the flipper way
        """

        with open("fastio.bin", "w") as f:
            f.write(RAW_Data)
            f.flush()

        self.args["mode"] = "flp"
        self.args["pin"] = pin

        self.__launchProcess__()

        self._process_.wait()

        os.remove("fastio.bin")

    def send(self, pin, bits, ns=1000):
        """
        transmit bits to a pin

        if `bits` is a list,   write it to a .bin file for the `pio` executable

        if `bits` is a string, open that as a path
        """

        if type(bits) == str:
            self.args["file"] = bits
        else:
            with open("fastio.bin", "wb") as f:
                f.write(
                    bitToByte(
                        ''.join([str(x) for x in bits])
                    )
                )
                f.flush()
        
            self.args["file"] = "fastio.bin"

        self.args["mode"] = "tx"
        self.args["pin"] = pin
        self.args["sleep"] = ns

        self.__launchProcess__()

        self._process_.wait()

        if type(bits) == list:
            os.remove("fastio.bin")


    def readSamples(self, pin, samples, output=None):
        """
        Read X amount of samples.
        This function *is* blocking.
        """

        self.args["pin"] = pin
        self.args["samples"] = samples
        self.args["mode"] = "rx"
        
        if output != None:
            self.args["file"] = output

        self.__launchProcess__()

        self._process_.wait()

        if output == None: # output file was not set
            return self.__parseBin__()
        else: # output file was set
            return self.__parseBin__(binf=output)
    
    def infread(self, pin):
        """
        Read pin X till death (by self.close()).
        Non-blocking.
        """

        self.args["pin"] = pin
        self.args["samples"] = "-1"
        self.args["mode"] = "rx"

        self.__launchProcess__()
        
    def close(self):
        """
        Close program, if there is one, running.
        """
        self._process_.send_signal(15)
        self._process_.wait()
        return self.__parseBin__()
    
    def setHZ(self, hz):
        """
        set polling rate to X hz
        """

        self.args["sleep"] = int(hz2NS(hz)-500 if hz2NS(hz)-500 > 0 else 0)
        print("[+] set PIO sleep to {}ns".format(hz2NS(hz)-500))

    def setNS(self, ns):
        """
        set polling rate to X nanoseconds (min is 500ns, overhead)
        """
        self.args["sleep"] = int(ns-500 if ns-500 > 0 else 0)
        print("[+] set PIO sleep to {}ns".format(ns))

    def __launchProcess__(self) -> None:
        """
        launch pio program
        """

        cmd = [self._executable_] + self.__compileArgs__()

        print("[+] {}".format(' '.join(cmd)))

        self._process_ = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        
        # process is started, reset args
        self.args = self.defaultArgs

    def __compileArgs__(self) -> list:
        """
        compile args to one list for Popen
        """
        x = []

        for param,val in self.args.items():
            x.append("--"+param)
            x.append(str(val))

        return x
    
    def __parseBin__(self, binf="samples.bin") -> str:
        """parse bin file to bits"""
        bits = []

        with open(binf, "rb") as f:
            byts = f.read()

        for byte in byts:
            bits += [int(x) for x in format(byte, '08b')]

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