class classA():
    def __init__(self):
        self.strA = "Hello World!"
        print(self.strA)

    def initialize(self):
        self.strA = "UNCHI"
        self.strB = "UNKO"
        stringB = 'shit'
        print(self.strA)
        print(self.strB)
        print(stringB)

    def init(self):
        print(self.strB)
        print(stringB)


test = classA()
test.initialize()
test.init()