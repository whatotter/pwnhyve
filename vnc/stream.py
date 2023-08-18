from tkinter import *
from PIL import ImageTk, Image, ImageOps
import socket
import base64
import sys
import io
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect((sys.argv[1], 11198))
s.settimeout(None)

class b:
    b64string = None

def getImg():
    data = s.recv(2048 * 8).decode('utf-8')

    try:
        img = Image.open(io.BytesIO(base64.b64decode(data)))
        return ImageOps.invert(img.resize([300, 162]))
    except (ConnectionAbortedError, ConnectionResetError):
        quit()
    except:
        time.sleep(0.1)
        return getImg() # call itself AGAIN
    
def sendStream(key):
    print("keypress")
    if key in ["up", "left", "right", "down", "1", "2", "3", "press"]:
        print("sent")
        s.sendall(key.encode('utf-8'))
        return True
    else:
        print("not sent")
        return None

root = Tk()
root.geometry("581x268")

#bgI = PhotoImage(file="./oled.png")

image = Image.open('./oled2.png')
# The (450, 350) is (height, width)
bgI = ImageTk.PhotoImage(image)

bg = Label(root, image=bgI)
bg.pack()

# Create a frame
app = Frame(root, bg="white")
app.place(x=136, y=69)
#app.grid()
# Create a label in the frame
lmain = Label(app)
lmain.grid()

# joystick

leftIMG = PhotoImage(file="./buttons/left.png")
rightIMG = PhotoImage(file="./buttons/right.png")
upIMG = PhotoImage(file="./buttons/up.png")
downIMG = PhotoImage(file="./buttons/down.png")
pressIMG = PhotoImage(file="./buttons/press.png")

left = Button(root, text="--------", command=lambda: sendStream("left"),
                 image=leftIMG, relief=FLAT, bd=0, takefocus=False, borderwidth=0, highlightthickness=0
                 )

down = Button(root, text="#\n#\n#\n#", command=lambda: sendStream("down"),
                 image=downIMG, relief=FLAT, bd=0, takefocus=False, borderwidth=0, highlightthickness=0
                 )

right = Button(root, text="--------", command=lambda: sendStream("right"),
                 image=rightIMG, relief=FLAT, bd=0, takefocus=False, borderwidth=0, highlightthickness=0
                 )

up = Button(root, text="#\n#\n#\n#", command=lambda: sendStream("up"),
                 image=upIMG, relief=FLAT, bd=0, takefocus=False, borderwidth=0, highlightthickness=0
                 )

press = Button(root, text="-#-", command=lambda: sendStream("press"),
                 image=pressIMG, relief=FLAT, bd=0, takefocus=False, borderwidth=0, highlightthickness=0
                 )

left.place(x=8, y=76+21)
down.place(x=10+14, y=152)
right.place(x=82, y=76+18)
up.place(x=9+20, y=76)
press.place(x=53, y=123)

# right keys

buttonIMG = PhotoImage(file="./buttons/button.png")

key1 = Button(root, text="--KEY1-", command=lambda: sendStream("1"),
               image=buttonIMG, borderwidth=0, relief=FLAT, bd=0, highlightthickness=0
               )


key2 = Button(root, text="--KEY2-", command=lambda: sendStream("2"),
               image=buttonIMG, borderwidth=0, relief=FLAT, bd=0, highlightthickness=0
               )


key3 = Button(root, text="--KEY3-", command=lambda: sendStream("3"),
               image=buttonIMG, borderwidth=0, relief=FLAT, bd=0, highlightthickness=0
               )

key1.place(x=468, y=70)
key2.place(x=468, y=128-2)
key3.place(x=468, y=182-2)

# function for video streaming
def video_stream():
    img = getImg()
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)
    lmain.after(50, video_stream) 

video_stream()
root.mainloop()