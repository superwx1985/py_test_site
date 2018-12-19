class VicStep:
    def __init__(self, name):
        self.name = name
        self._force_stop = False

    @property
    def force_stop(self):
        if self._force_stop:
            return True
        else:
            return False

    @force_stop.setter
    def force_stop(self, v):
        self._force_stop = v

import time

def a(vicstep, force_stop):
    print(vicstep.force_stop, force_stop)
    vicstep.force_stop = True
    print(vicstep.force_stop, force_stop)

vs = VicStep(1)
a(vs, vs.force_stop)