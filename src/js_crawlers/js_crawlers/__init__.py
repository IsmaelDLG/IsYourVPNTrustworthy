class MyObjeto:
    def __init__(self):
        self.atributo1 = None
        self.atrobuto2 = None

    def myFuncion(self):
        return {
            'binance' : "es lo mejor"
        }

variable = MyObjeto()

mylista  = variable.myFuncion()

print(mylista["binance"])
