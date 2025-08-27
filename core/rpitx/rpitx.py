import os
import signal
import subprocess
import threading
import typing

class PiFMRds:
    def __init__(self, location="../PiFmAdv/pi_fm_adv") -> None:
        self.location = location
        self.freq = 102.5
        self.ps = "pwnhyve.xyz"
        self.rt = "pwnhyve.xyz"
        self.power = 30

        self.thread = None
        pass

    def stop(self):
        if self.thread is not None:
            self.thread.send_signal(signal.SIGINT)
            self.thread = None
            return True
        
        return None

    def play(self, audio:str):
        try:
            assert audio.endswith(".wav")
        except:
            raise FileNotFoundError("Audio file must be a wav file")
        
        try:
            assert os.path.exists(audio)
        except:
            raise FileNotFoundError("{} doesn't exist".format(audio))
        
        try:
            assert self.freq > 50 and 160 > self.freq
        except:
            raise ValueError("Frequency must be inbetween 50mhz and 160mhz")
        
        subprocess.Popen(["pwd"])

        self.thread = subprocess.Popen([self.location, 
                                        "--audio", audio,
                                        "--freq", str(self.freq),
                                        "--ps", self.ps,
                                        "--rt", self.rt,
                                        #"--dev", "25000",
                                        "--mpx", str(self.power)
                                        ]
            )
        
        return self.thread
    
class rpitxTypes:
    class OOK:
        modType_OOK = 0 # OOK
        modType_OOK_PWM = 1 # OOK PWM
        modType_OOK_PPM = 2 # OOK PPM
    
class rpitx():
    """
    send real i/q data
    """
    def __init__(self, folder="../rpitx") -> None:
        self.folder = folder
        self.freq = "434.0M"
        self.threaded = False
        self.sudo = True
        pass

    def __getExecutable__(self, executable:str) -> str:
        return os.path.join(self.folder, executable)
    
    def __runCommand__(self, command:str) -> typing.Union[threading.Thread, int]: #i need to start using type annotations more
        if self.sudo: 
            command = "sudo " + command
            
        if self.threaded:
            thread = threading.Thread(target=os.system, args=(command,), daemon=True)
            thread.start()
            return thread
        else:
            return subprocess.getstatusoutput(command)

    def __arg__(self, key:str, arg) -> str:
        if arg == None or arg == False:
            return ""
        else:
            return "{} {}".format(key, arg)

    def __mergeArgs__(self, args:list) -> str:
        arglist = []

        for arg in args:
            if arg == "":
                continue
            else:
                arglist.append(arg)

        return ' '.join(arglist)

    def setFrequency(self, frequency:str):
        """
        sets RPITX frequency

        @frequency: frequency as a string, e.g. 434.0M (434mhz) or 125.0K (125khz) or 1.20g (1.2ghz)
        """
        frequency = frequency.upper()

        try:
            assert "G" == frequency[-1] or "M" == frequency[-1] or "K" == frequency[-1]
        except AssertionError:
            raise ValueError("Frequency must end with G,M,K ")

        self.freq = frequency

    def OOK(self, bits, 
            downBitDuration=None, 
            upBitDuration=None, 
            repeats=None, 
            bitGap=None,
            modType=None
            ):
        """
        send OOK modulated data

        @bits: binary bits to transmit
        @downBitDuration: time (in us) of how long a `0` lasts (default 500us)
        @upBitDuration: time (in us) of how long a `1` lasts (defualt 250us)
        @repeats: # of times to repeat all bits again (default 3)
        @bitGap: gap between bits being transmitted (default 500us)
        @modType: modulation type (use rpitxTypes.OOK for this, default 0)
        """

        # sudo sendook -f {self.freq} -0 {kwargs}

        args = self.__mergeArgs__([
            self.__getExecutable__("sendook"),
            "-f {}".format(self.freq),
            self.__arg__("-0", downBitDuration),
            self.__arg__("-1", upBitDuration),
            self.__arg__("-g", bitGap),
            self.__arg__("-r", repeats),
            self.__arg__("-m", modType),
            bits
        ])

        return self.__runCommand__(args)