from core.plugin import BasePwnhyvePlugin

class PWNTestOne(BasePwnhyvePlugin):
    def command(self, draw, disp, image, GPIO):
        print("ok")

    def balls(self, draw, disp, image, GPIO):
        print("ok")

    def sack(self, draw, disp, image, GPIO):
        print("ok")

class PWNTestTwo(BasePwnhyvePlugin):
    def chicken(self, draw, disp, image, GPIO):
        print("ok")