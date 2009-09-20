# Richard Darst, May 2009
# David M. Creswick, Sept 2009

import math

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
        if self.n == 0: return float('nan')
        return math.sqrt(self._M2 / self.n)
    @property
    def stdsample(self):
        """Sample Variance"""
        if self.n <= 1: return float('nan')
        return math.sqrt(self._M2 / (self.n-1))
    @property
    def var(self):
        """Population Standard Deviation"""
        if self.n == 0: return float('nan')
        return self._M2 / self.n
    @property
    def varsample(self):
        """Sample Standard Deviation"""
        if self.n <= 1: return float('nan')
        return self._M2 / (self.n-1)

def extended_euclidean_algorithm(a, b):
    """given integers a and b , I return the tuple (x, y, gcd(a,b))
    such that x*a + y*b = gcd(a,b)

    Generally speaking, the algorithm should work over any principal
    ideal domain, so you can probably pass any pair of python object
    that act like members of a principal ideal domain.

    """
    q, r = divmod(a,b)
    if r == 0:
        return 0, 1, b
    else:
        x, y, gcd = extended_euclidean_algorithm(b, r)
        return y, (x-y*q), gcd

def gcd(a, b):
    '''finds greatest common denominator of a and b
    '''
    _, _, gcd = extended_euclidean_algorithm(a,b)
    return gcd

def product(seq):
    it = iter(seq)
    x = it.next()
    for y in it:
        x *= y
    return x

def chinese_remainder_algorithm(congruences):
    '''Chinese remainder algorithm

    Given a list of (n_i, a_i) tuples, this function finds an integer
    x such that x mod n_i = a_i for all n_i, a_i in the list of
    congruences.

    eg, chinese_remainder_algorithm([(3,2),(4,3),(5,1)]) returns 11
    because 11 mod 3 is 2, 11 mod 4 is 3, and 11 mod 5 is 1

    '''
    N = product([n for n,_ in congruences])
    c = 0
    for n,a in congruences:
        _, y, gcd = extended_euclidean_algorithm(n, N/n)
        assert gcd == 1
        e = y*N/n
        c += a*e
    return c % N
