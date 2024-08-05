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

import asyncio
from websockets.sync.client import connect



ip = input("ip: ") if len(sys.argv) == 1 else sys.argv[1]
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
        s = True
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

        self.pixmap = QPixmap()
        #self.label.setPixmap(self.pixmap.scaled(128*2, 64*2))

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
            key = keys.get(event.key())
            print(key)
            if key not in self.buttonQ:
                self.buttonQ.append(key)
                print('button add: {}'.format(self.buttonQ))


        super().keyReleaseEvent(event)

    def display_frame(self): 
        global ip

        haveibeenfucked = False

        while True:
            try:
                with connect("ws://{}:8765".format(ip)) as websocket:
                    if haveibeenfucked:
                        self.status.setText("RECONNECTED.")
                        haveibeenfucked = False

                    websocket.send("R")
                    while True:
                        if len(self.buttonQ) != 0:
                            for x in self.buttonQ:
                                websocket.send(x)
                                time.sleep(0.01)
                            
                            self.buttonQ.clear()

                        try:
                            rawresp = websocket.recv(0)
                        except TimeoutError:
                            continue
                        except:
                            self.status.setText("DISCONNECTED. ATTEMPTING RECONNECT..")
                            haveibeenfucked = True
                            break

                        rsp = json.loads(rawresp)

                        frame = rsp["frame"].encode('ascii')
                        log = base64.b64decode(rsp['log'].encode('ascii')).decode('ascii')

                        if log.strip() != "":
                            clog.append(log.strip())

                        ret = True
                        if frame is None:
                            ret = False

                        if ret:
                            ba = QByteArray.fromBase64(frame)
                            if self.pixmap.loadFromData(ba, "JPEG"):
                                self.label.setPixmap(self.pixmap.scaled(128*2, 64*2))
                                pass

                            #self.update()  # Trigger PyQt window update

                            #time.sleep(self.sleeptime/2)

                        #await rawresp

                        time.sleep(0.001)
            except:
                print("failed to recconect")
                time.sleep(1)
            


async def main():
    app = QApplication([])
    z = QFontDatabase.addApplicationFont("haxrcorp-4089.ttf")

    padding = 14

    stream = VideoWindow(paddingX=round(padding/2), paddingY=round(padding/2))
    stream.resize(581+padding,335+padding)
    stream.show()

    threading.Thread(target=stream.display_frame,daemon=True).start()

    try:
        while True:
            app.processEvents()  # Handle PyQt events
    except KeyboardInterrupt:
        pass

asyncio.run(main())