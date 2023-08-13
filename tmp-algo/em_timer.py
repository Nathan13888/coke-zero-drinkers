import time

class Timer:
    #------------------------------------------------------------------
    def __init__(self):
        self.timerStart = time.time()
    #------------------------------------------------------------------
    def reset(self):
        self.timerStart = time.time()
    #------------------------------------------------------------------
    def timeLeft(self):
        return 5 - self.timePassed()
    #------------------------------------------------------------------
    def timePassed(self):
        return time.time()-self.timerStart
    #------------------------------------------------------------------
