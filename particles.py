class Particles:

    def __init__(self, position, speed, type):
        self.position = position
        self.speed = speed
        self.type = type

    @property
    def position(self):
        return self.position

    @position.setter
    def position(self, position):
        self.position = position

    @property
    def speed(self):
        return self.speed
    
    @speed.setter
    def speed(self, speed):
        self.speed = speed

    @property
    def type(self):
        return self.type

    @type.setter
    def type(self, type):
        self.type = type