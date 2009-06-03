# Richard Darst, May 2009


def cartesianproduct(*args):
    """Cartesian product of iteratables given as arguments.

    This implementation thanks to MrGreen.
    """
    if len(args) == 0:
        yield ()
    else:
        for x in args[0]:
            for xs in cartesian_product_mrgreen2(*args[1:]):
                yield (x,) + xs

def chooseNEnumerate(objs, number=1):
    """Iterator over all posibilities of choosing `number` of `objs`

    This *exhaustively lists* all options, not providing overall
    statistics.
    """
    # by Richard Darst
    if number == 0:
        yield ()
        return

    for i, obj in enumerate(objs):
        otherobjs = objs[:i] + objs[i+1:]
        #print " current", obj, otherobjs
        for conditional_selections in chooseNEnumerate(otherobjs, number-1):
            #print " others", conditional_selections
            yield ( obj, ) + conditional_selections



class Averager(object):
    """Numerically Stable Averager

    Calculate averages and standard deviations in a numerically stable way.

    From the 'On-Line Algorithm' from
    http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
    """
    def __init__(self):
        self.n       = 0
        self._mean    = 0.   # mean
        self._M2     = 0.   # variance accumulator
        #self._var_n  = 0.
        #self._var_n1 = 0.
    def add(self, value):
        """Add a new number to the dataset.
        """
        n = self.n + 1
        delta = value - self._mean
        mean = self._mean + delta/n
        M2 = self._M2 + delta*(value - mean)
        self.n = n
        self._mean = mean
        self._M2 = M2

    @property
    def mean(self):
        """Mean"""
        return self._mean
    @property
    def std(self):
        """Population Variance"""
        return math.sqrt(self._M2 / self.n)
    @property
    def stdsample(self):
        """Sample Variance"""
        return math.sqrt(self._M2 / (self.n-1))
    @property
    def var(self):
        """Population Standard Deviation"""
        return self._M2 / self.n
    @property
    def varsample(self):
        """Sample Standard Deviation"""
        return self._M2 / (self.n-1)
