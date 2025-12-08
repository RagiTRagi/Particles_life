class Particles:

    def __init__(self, position, speed, ptype):
        self._position = position
        self._speed = speed
        self._ptype = ptype

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position

    @property
    def speed(self):
        return self._speed
    
    @speed.setter
    def speed(self, speed):
        self._speed = speed

    @property
    def ptype(self):
        return self._ptype

    @ptype.setter
    def ptype(self, ptype):
        self._ptype = ptype