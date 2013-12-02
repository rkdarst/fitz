# Richard Darst, July 2011

from math import log, exp

class LogInterval(object):
    """
    interval - how many
    """
    # How many
    interval = 10
    def __init__(self, interval=10, number=10, initial=1,
                 low=None, high=None):
        self.interval = interval
        self.initial = initial
        self.number = number
        #self.every = interval
        self.expConstant = exp(log(interval) / number)
    def value(self, index):
        return self.initial * self.expConstant**index
    def index(self, value):
        return log(value/self.initial) / (log(self.interval)/self.number)

    def iter(start, maxValue=None):
        index = startAt
        while True:
            value = self.value(index)
            yield value
            index += 1

            if maxValue is not None and maxValue > index :
                break

if __name__ == "__main__":
    # add tests here
    pass
