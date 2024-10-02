import os
import struct
import subprocess
import threading
import time

def hz2NS(hz):
    if hz <= 0:
        raise ValueError("frequency must be greater than 0hz")
    
    return (1 / hz) * 1e9

class FastIO:
    def __init__(self) -> None:
        self.delayNS = 0

        self._executable_ = "./pio"
        self._process_ = None
        self.defaultArgs = {
            "samples": "-1",
            "output": "samples.bin",
            "pin": "-1",
            "mode": "rx",
            "sleep": "7500"
        }
        self.args = self.defaultArgs

        pass

    def readSamples(self, pin, samples):
        """
        Read X amount of samples.
        """

        self.args["pin"] = pin
        self.args["samples"] = samples
        self.args["mode"] = "rx"

        self.__launchProcess__()

        self._process_.wait()

        return self.__parseBin__()
    
    def infread(self, pin):
        """
        Read pin X till ^C death (by self.close()).
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

        self.args["sleep"] = hz2NS(hz)
        print("[+] set PIO sleep to {}ns".format(hz2NS(hz)))

    def setNS(self, ns):
        """
        set polling rate to X nanoseconds (0 = 500 nanoseconds, there's overhead)
        """
        self.args["sleep"] = ns
        print("[+] set PIO sleep to {}ns".format(ns))

    def __launchProcess__(self) -> None:
        """
        launch pio program
        """

        cmd = [self._executable_] + self.__compileArgs__()

        self._process_ = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        
        # process is started, reset args
        self.args = self.defaultArgs
        
    def __sendC__(self) -> None:
        """
        send ^C to currently open process
        """

        if self._process_ != None:
            self.__sendByte__(b'\x03')

    def __sendByte__(self, byte) -> None:
        """
        send a byte to process stdin
        """

        self._process_.stdin.write(byte)
        self._process_.stdin.flush()

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
        bits = ""

        with open(binf, "rb") as f:
            byts = f.read()

        for byte in byts:
            bits += format(byte, '08b')

        os.remove(binf)

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

    bits = io.readSamples(22, 11221)
    print("{} bits".format(len(bits)))

    io.setNS(0)
    
    io.infread(22)
    time.sleep(0.1)
    bits = io.close()
    print("{} bits".format(len(bits)))