sctext = ""
def scText(text, caption):
    global sctext

    s = (sctext+"\n"+str(text)).strip().split("\n")
    lines = len(s)

    print(s)

    if lines > 5:
        while len(s) > 5:
            s.pop(0)
    elif lines != 5:
        while len(s) != 5:
            s.append("\n")

    print(s)

    s.append(caption)
    
    print(s)

    return ''.join(s)

z = scText("abcd", "fortnite")
b = 0
for ln in z.split("\n"):
    print("{}: {}".format(b, ln))
    b += 1