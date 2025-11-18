class Particles:

    def __init__(self, position, speed, ptype):
        self.position = position
        self.speed = speed
        self.type = ptype

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
    def ptype(self):
        return self.ptype

    @type.setter
    def ptype(self, ptype):
        self.ptype = ptype