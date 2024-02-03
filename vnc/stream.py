import json
import os
import threading
from tkinter import *
from PIL import ImageTk, Image, ImageOps
import socket
import base64
import sys
import io
import time

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QByteArray, QPoint
import base64


ip = sys.argv[1]
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
s.connect((ip, 11198))
s.settimeout(0.25)
#s.setblocking(False)

clog = []

def dumpAndOpenLog():
    global clog

    for x in clog.copy():
        if x == " ":
            clog.pop(clog.index(x))

    with open("log.txt", "w") as f:
        f.write('\n'.join(clog))

    os.system("start ./log.txt")

class VideoWindow(QWidget):
    buttonQ = []
    def __init__(self, paddingX=4, paddingY=4):
        global s
        super().__init__()
        self.setWindowTitle("Video Display")
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.paddingX = paddingX
        self.paddingY = paddingY
        self.serverExited = False

        """
        p = self.palette()
        p.setColor(self.backgroundRole(), "#080808")
        self.setPalette(p)
        """

        self.setStyleSheet("background-color: #080808; font-family: haxrcorp 4089; color: white; border-radius: 4px")


        # if you see a 1==1 its for readability in vscode so i can close certain tabs

        if 1==1: # disp keys
            self.box = QFrame(self)
            self.label = QLabel(self)

            self.box.move(paddingX, paddingY+24)

            self.down = QPushButton(self)
            self.right = QPushButton(self)
            self.left = QPushButton(self)
            self.up = QPushButton(self)

            self.mid = QPushButton(self)

            self.one = QPushButton(self)
            self.two = QPushButton(self)
            self.three = QPushButton(self)

        if 1==1: # logs n such
            self.logs = QPushButton(self)
            self.logs.setStyleSheet("""
    color: #eee; 
    background-color: #303030; 
    border-radius: 4px;
    font-size: 24px;
    padding: 8px
                                    """.strip()) # my css skills are really showing
            #self.logs.setFont(QFont('Pixel Operator Mono'))
            self.logs.setText("LOGS")
            self.logs.move(paddingX, 274+paddingY+24)
            self.logs.resize(96, 32)
            self.logs.clicked.connect(lambda: dumpAndOpenLog())
            self.logs.setFocusPolicy(Qt.NoFocus)

            self.status = QLabel(self)
            self.status.resize(484-paddingX, 32)
            self.status.move(104+paddingX, 274+paddingY+24)
            self.status.setStyleSheet("background-color: red; padding: 8px; color: #eee; background-color: #303030; font-size: 24px; border-radius: 4px;")

        self.setupButtons()

        w,h = (581, 268)
        self.box.setStyleSheet("background-image: url('./oled2.png'); background-attachment: fixed; border-radius: 8px; border: 4px solid #303030;")
        self.box.resize(w, h)  # Set initial size
        self.label.move(140+paddingX, 73+paddingY+24)
        self.label.resize(304, round(64*2.6, None))
        self.label.setScaledContents(True)

        if 1==1: # window keys
            self.exit = QPushButton(self)
            self.exit.resize(24,24)
            self.exit.setText("X")
            self.exit.setStyleSheet("background-color: transparent; font-size: 38px")
            self.exit.clicked.connect(lambda: sys.exit())
            self.exit.setFocusPolicy(Qt.NoFocus)

            self.min = QPushButton(self)
            self.min.resize(24,24)
            self.min.setText("_")
            self.min.setStyleSheet("background-color: transparent; font-size: 38px")
            self.min.clicked.connect(self.showMinimized)
            self.min.setFocusPolicy(Qt.NoFocus)

            self.min.move( 581-36,  4)
            self.exit.move(581-14,  4)


        self.mods = []
        self.pressedKeys = []

        self.lockCursor = False

        self.recentMouseCoords = (0, 0)

        self.sleeptime = round(1000/120, ndigits=1) / 1000

        if s:
            self.status.setText("CONNECTED.")

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if 32 > event.y():
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def setupButtons(self):

        # joystick directions
        self.up.move(   52+self.paddingX+4, 70 +self.paddingY+28)
        self.down.move( 52+self.paddingX+4, 155+self.paddingY+28)
        self.right.move(85+self.paddingX+4, 120+self.paddingY+28)
        self.left.move(  0+self.paddingX+4, 120+self.paddingY+28)
        self.mid.move(  52+self.paddingX+4, 120+self.paddingY+28)

        self.up.resize(35, 50)
        self.down.resize(35, 50)
        self.right.resize(50, 35)
        self.left.resize(50, 35)
        self.mid.resize(34, 34)
        

        # right side buttons
        self.one.move(  482+self.paddingX+4, 72 +self.paddingY+28)
        self.two.move(  482+self.paddingX+4, 126+self.paddingY+28)
        self.three.move(482+self.paddingX+4, 180+self.paddingY+28)

        self.one.resize(52, 30)
        self.two.resize(52, 30)
        self.three.resize(52, 30)

        # make all transparent

        stylesheet = "background: transparent;"
        self.up   .setStyleSheet(stylesheet)
        self.down .setStyleSheet(stylesheet)
        self.right.setStyleSheet(stylesheet)
        self.left .setStyleSheet(stylesheet)
        self.mid  .setStyleSheet(stylesheet)
        self.one  .setStyleSheet(stylesheet)
        self.two  .setStyleSheet(stylesheet)
        self.three.setStyleSheet(stylesheet)

        # do callbaks
        self.up.clicked.connect(lambda:    self.buttonQ.append("up"))
        self.down.clicked.connect(lambda:  self.buttonQ.append("down"))
        self.right.clicked.connect(lambda: self.buttonQ.append("right"))
        self.left.clicked.connect(lambda:  self.buttonQ.append("left"))
        self.mid.clicked.connect(lambda:   self.buttonQ.append("press"))
        self.one.clicked.connect(lambda:   self.buttonQ.append("1"))
        self.two.clicked.connect(lambda:   self.buttonQ.append("2"))
        self.three.clicked.connect(lambda: self.buttonQ.append("3"))

        self.up   .setFocusPolicy(Qt.NoFocus)
        self.down .setFocusPolicy(Qt.NoFocus)
        self.right.setFocusPolicy(Qt.NoFocus)
        self.left .setFocusPolicy(Qt.NoFocus)
        self.mid  .setFocusPolicy(Qt.NoFocus)
        self.one  .setFocusPolicy(Qt.NoFocus)
        self.two  .setFocusPolicy(Qt.NoFocus)
        self.three.setFocusPolicy(Qt.NoFocus)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.palette().window())
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)  # Adjust radius as needed

    def keyReleaseEvent(self, event):
        global s

        keys = {
            16777237: "down",
            16777235: "up",
            16777236: "right",
            16777234: "left",

            47: "press",

            49: "1",
            50: "2",
            51: "3",
        }

        if keys.get(event.key(), False):
            print(keys.get(event.key()))
            self.buttonQ.append(keys.get(event.key()))

        super().keyReleaseEvent(event)

    def display_frame(self): 
        global s
        while True:
            if self.serverExited:
                try:
                    s.connect((sys.argv[1], 11198))
                    s.settimeout(0.25)
                    time.sleep(2.5)
                    self.status.setText("RECONNECTED.")
                    self.serverExited = False
                except (TimeoutError, ConnectionAbortedError, ConnectionRefusedError):
                    print('failed reconnection')
                    time.sleep(1)

                continue
            else:
                try:
                    frame = s.recv(32)
                except (TimeoutError):
                    frame = None
                except:
                    s.close()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.status.setText("SERVER EXITED. ATTEMPTING RECONNECT...")
                    self.serverExited = True
                    continue
                #ret, frame = True, self.cap.read()

                print(frame)
                if frame != None:
                    if frame == b"\x01\r\n":
                        print("client hello")
                        s.sendall(b'\x02')
                        continue
                    else:
                        print(frame)
                        if frame == b'':
                            print('server exited')
                            self.status.setText("SERVER EXITED. ATTEMPTING RECONNECT...")
                            s.close()

                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.settimeout(1)

                            self.serverExited = True
                            
                        if "L:" in frame.decode('ascii'):
                            # for fragmentation
                            buffer = int(frame.decode('ascii').replace("L:", "")) # me when i refuse to use regex
                            print("bufsize: {}".format(buffer*2))
                            s.sendall(b'\x01')
                            print('sent x01')

                            data = b''
                            while len(data) != buffer:
                                try:
                                    z = s.recv(buffer)
                                except:
                                    continue # broken frame
                                data += z

                            assert len(data) == buffer
                            
                            array = json.loads(data.decode('ascii'))

                            frame = array["frame"].encode('ascii')
                            log = base64.b64decode(array['log'].encode('ascii')).decode('ascii')

                            if log.strip() != "":
                                clog.append(log.strip())
                                print(log)

                            print("{} = {}".format(len(frame), buffer))

                    ret = True
                    if frame is None:
                        ret = False

                    if ret:
                        ba = QByteArray.fromBase64(frame)
                        pixmap = QPixmap()
                        if pixmap.loadFromData(ba, "JPEG"):
                            self.label.setPixmap(pixmap.scaled(128*2, 64*2))

                        self.update()  # Trigger PyQt window update

                        #time.sleep(self.sleeptime/2)

                if len(self.buttonQ) != 0:
                    for x in self.buttonQ:
                        s.sendall(x.encode('ascii'))
                        if s.recv(16) == b"\x01":
                            print('sent key {}'.format(x))

                    self.buttonQ.clear()
                else:
                    s.sendall(b'\x00')


def sendStream(key):
    print("keypress")
    if key in ["up", "left", "right", "down", "1", "2", "3", "press"]:
        print("sent")
        s.sendall(key.encode('utf-8'))
        return True
    else:
        print("not sent")
        return None

app = QApplication([])
z = QFontDatabase.addApplicationFont("haxrcorp-4089.ttf")

padding = 14

stream = VideoWindow(paddingX=round(padding/2), paddingY=round(padding/2))
stream.resize(581+padding,335+padding)
stream.show()

threading.Thread(target=stream.display_frame, daemon=True).start()
while True:
    app.processEvents()  # Handle PyQt events