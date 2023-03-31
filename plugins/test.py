from core.SH1106.screen import enterText


config = { 
    # you can have this in an external file, aslong as main file gets it in dictionary format
    # this is for your command help n stuff
    "test": "test",

    "icons": {
        "hello": "./core/icons/zzz.bmp"
    }
}

def test(args):
    canvas, display, image, GPIO = args[0], args[1], args[2], args[3]

    enterText(canvas, display, image, GPIO)


def functions():
    return config