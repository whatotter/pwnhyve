import os
import signal
import subprocess
import threading

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