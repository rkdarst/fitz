# Richard Darst, May 2009
# David M. Creswick, Sept 2009

import collections
import math
import numpy
import numpy.linalg
import numpy as np

def cartesianproduct(*args):
    """Cartesian product of iteratables given as arguments.

    This implementation thanks to MrGreen.
    """
    if len(args) == 0:
        yield ()
    else:
        for x in args[0]:
            for xs in cartesianproduct(*args[1:]):
                yield (x,) + xs

# FIXME: this is actually permutations.
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

    The optional initialization argument datatype= should be a
    generator function which returns zeros of the type being averaged.
    For example, to average numpy arrays of ten values, use:
      Averager(datatype=lambda: numpy.zeros(10))
    """
    def __init__(self, datatype=float):
        self._n      = 0
        self._mean   = datatype()   # mean
        self._M2     = datatype()   # variance accumulator
    def __setstate__(self, state):
        if 'n' in state:
            state['_n'] = state['n']
            del state['n']
        self.__dict__.update(state)
    def add(self, value):
        """Add a new number to the dataset.
        """
        if isinstance(value, Averager):
            # Add a sub-averager
            return self._add_child(value)
        n = self.n + 1
        delta = value - self._mean
        mean = self._mean + delta/n
        M2 = self._M2 + delta*(value - mean)
        self._n = n
        self._mean = mean
        self._M2 = M2
        return self
    __iadd__ = add

    def _add_child(self, child):
        if hasattr(self, "_child"):
            self._child.add(child)
        else:
            self._child = child
        return self

    @property
    def n(self):
        """Number of points"""
        if hasattr(self, "_child"):
            return self._n + self._child.n
        return self._n
    @property
    def mean(self):
        """Mean"""
        if hasattr(self, "_child"):
            #if self._n > 1e3 and self._child.n > 1e3:
            #    # Large value one
            #    return (self._n*self._mean + self._child.n*self._child.mean) /\
            #           (self._n + self._child.n)

            delta = self._child.mean - self._mean
            return self._mean + delta * self._child.n/(self._n+self._child.n)
        return self._mean
    @property
    def M2(self):
        """M2 algorithm parameter"""
        if hasattr(self, "_child"):
            delta = self._child.mean - self._mean
            return self._M2 + self._child.M2 + \
                   delta**2 * (self._n*self._child.n)/(self._n+self._child.n)
        return self._M2
    @property
    def std(self):
        """Population standard deviation"""
        if self.n == 0: return float('nan')
        return math.sqrt(self.M2 / self.n)
    @property
    def stdsample(self):
        """Sample standard deviation"""
        if self.n <= 1: return float('nan')
        return math.sqrt(self.M2 / (self.n-1))
    @property
    def stdmean(self):
        """(Sample) standard deviation of the mean.  std / sqrt(n)"""
        if self.n <= 1: return float('nan')
        return math.sqrt(self.M2 / ((self.n-1)*self.n))
    @property
    def var(self):
        """Population variance"""
        if self.n == 0: return float('nan')
        return self.M2 / self.n
    @property
    def varsample(self):
        """Sample variance"""
        if self.n <= 1: return float('nan')
        return self.M2 / (self.n-1)
    def proxy(self, expr):
        """Proxy for computing other"""
        return _AvgProxy(main=self, expr=expr)
    def proxygen(self, expr):
        return lambda: self.proxy(expr=expr)
class _AvgProxy(object):
    def __init__(self, main, expr):
        self.main = main
        self.expr = expr
    def add(self, x):
        raise "You can't add values to proxy objects"
    @property
    def mean(self):
        return eval(self.expr, dict(o=self.main))

class AutoAverager(object):
    def __init__(self, datatype=float, newAverager=Averager,
                 depth=1, auto_proxy=[]):
        """
        if depth=1, then self[name] will be an Averager
        if depth=2, then self[name] will be AutoAverager...
                  ...and self[name2] will be an Averager
        and so on.

        newAverager is what the leaf averager object will be created
        with.  This should be replaced with AutoAverager.

        This will automatically make hierarchical averagers
        """
        self.datatype = datatype
        self.depth = depth
        self.newAverager = newAverager
        self.names = [ ]
        self.data = { }
        self.data_list = [ ]
        self.auto_proxy = auto_proxy
    def __getitem__(self, name, newAverager=None, do_proxy=True):
        # newAverager is used for proxy objects.
        if name not in self.data:
            if self.depth > 1:
                new = self.__class__(datatype=self.datatype,
                                     newAverager=self.newAverager,
                                     depth=self.depth-1,
                                     auto_proxy=self.auto_proxy,
                                     )
            else:
                if newAverager is not None:
                    new = newAverager()
                else:
                    new = self.newAverager(datatype=self.datatype)
            self.names.append(name)
            self.data[name] = new
            self.data_list.append(new)
            # Add auto-proxies (e.g. computing std dev?)
            if self.depth == 1 and not isinstance(new, _AvgProxy) and do_proxy:
                for suffix, expr in self.auto_proxy:
                    self.add_proxy(name, name+suffix, expr=expr)
        return self.data[name]
    get = __getitem__
    def add(self, name, val, do_proxy=True):
        self.get(name, do_proxy=do_proxy).add(val)
    def remove(self, name_or_index):
        if isinstance(name_or_index, int):
            name = self.names[-1]
            del self.data[name]
            del self.names[-1]
        else:
            del self.data[name]
            self.names.remove(name)
    def __iter__(self):
        for key in self.names:
            return (key, self.data[key])
    def add_proxy(self, name_orig, name_new, expr):
        """Add a proxy object.

        Example usage to add a standard deviation column:
        .add_proxy('q', 'q_std', 'o.stdmean')"""
        if name_new not in self.data:
            self.get(name_new, newAverager=self[name_orig].proxygen(expr))
    def column(self, name, attrname='mean'):
        assert self.depth == 2
        return [getattr(self.data[name_][name], attrname) for name_ in self.names]
    def column_names(self):
        return self.data[self.names[0]].names
    def table(self, attrname='mean'):
        assert self.depth == 2
        return zip(*(self.column(name, attrname=attrname)
                     for name in self.column_names()))
class _DerivProxy(_AvgProxy):
    def __init__(self, main, name, t):
        self.main = main
    def add(self, x):
        raise "You can't add values to proxy objects"
    @property
    def mean(self):
        idx = main.names.index(t)
        if idx == 0 or idx == len(main.names)-1:
            return float('nan')
        return (main[t+1][name].mean-main[t-1][name].mean)/2.

def _test_Averager():
    import random
    random.seed(13)
    rand = lambda : random.uniform(0, 10)
    a  = Averager()
    a_stack = [ ]
    for i in range(10):
        a_ = Averager()
        v1 = [ rand() for _ in range(100000) ]
        [ a.add(x)  for x in v1 ]
        [ a_.add(x) for x in v1 ]
        a_stack.append(a_)
    a1 = a_stack[0]
    for i in range(1, len(a_stack)):
        a_stack[i-1].add(a_stack[i])

    #a1 = Averager()
    #a2 = Averager()
    #a3 = Averager()
    #v1 = [ rand() for _ in range(10) ]
    #v2 = [ rand() for _ in range(10) ]
    #v3 = [ rand() for _ in range(10) ]
    #
    #[ a.add(x)  for x in v1 ]
    #[ a.add(x)  for x in v2 ]
    #[ a.add(x)  for x in v3 ]
    #[ a1.add(x)  for x in v1 ]
    #[ a2.add(x)  for x in v2 ]
    #[ a3.add(x)  for x in v3 ]
    #
    #a1.add(a2)
    #a2.add(a3)

    print a.mean, a1.mean, a.mean - a1.mean
    print a.M2,   a1.M2,   a.M2   - a1.M2
    print a.std,  a1.std,  a.std  - a1.std
    assert a.mean == a1.mean
    assert a.M2   == a1.M2
    assert a.std  == a1.std

def extended_euclidean_algorithm(a, b):
    """given integers a and b , I return the tuple (x, y, gcd(a,b))
    such that x*a + y*b = gcd(a,b)

    Generally speaking, the algorithm should work over any principal
    ideal domain, so you can probably pass any pair of python object
    that act like members of a principal ideal domain.


    Proof of correctness:
    The division algorithm asserts existence of integers q and r so
    that 0 <= r < b and
    
    (1)  a = q*b + r.
    
    If r == 0, then b divides a exactly, thus b is the gcd of a and
    b. Obviously x=0 and y=1. This handles the base case for the
    induction argument. So now assume r != 0 and run the extended
    euclidean algorithm on b and r to find integers x' and y' such
    that

    (2) x'*b + y'*r = gcd(b,r).

    The recursive application of the euclidean algorithm will
    eventually terminate becase 0 <= r < b, so at every iteration it
    is being applied to a pair of numbers that are strictly smaller
    than before.  Multiply eqn (1) by y' and substitute into (2) for
    y'*r to get

    y'*a + (x' - y'*q)*b = gcd(b,r).

    Due to eqn (1), gcd(b,r) = gcd(a,b). So the coefficients are
    x = y' and y = x' - y'*q.

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
    """Chinese remainder algorithm

    Given a list of (n_i, a_i) tuples where the n_i are all pairwise
    coprime, this function finds an integer x such that x mod n_i =
    a_i for all n_i, a_i in the list of congruences.

    eg, chinese_remainder_algorithm([(3,2),(4,3),(5,1)]) returns 11
    because 11 mod 3 is 2, 11 mod 4 is 3, and 11 mod 5 is 1

    Proof of correctness:
    If you have a collection of integers e_i that have the property that
    e_i mod n_j = 0 for i != j and e_i mod n_j = 1 for i = j, then
    (a_1*e_1 + a_2*e_2 + ... + a_k*e_k) mod n_i = a_i for all i.
    So the mystery number x is (a_1*e_1 + a_2*e_2 + ... + a_k*e_k).
    Now we just have to construct e_i that have those properties.
    Define N = n_1*n_2*...*n_k. Then N is divisible by n_i and N/n_i
    is relatively prime to n_i (because remember n_i is relatively
    prime to n_j for all i != j). The Euclidean algorithm can be
    used to find integers x and y so that x*n_i + y*N/n_i = 1. From
    this equation, you can tell that (y*N/n_i) mod n_i = 1. Since N/n_i
    has every n_j as a factor except n_i, (y*N/n_i) mod n_j = 0 for j != 1.
    We have found the e_i we needed, specifically, e_i = y*N/n_i.

    """
    N = product([n for n,_ in congruences])
    c = 0
    for n,a in congruences:
        _, y, gcd = extended_euclidean_algorithm(n, N/n)
        assert gcd == 1
        e = y*N/n
        c += a*e
    return c % N


def fact(x):
    """return the factorial of x"""
    return (1 if x==0 else x * fact(x-1))


def perm(l):
    """Generate all permuations of a list"""
    sz = len(l)
    if sz <= 1:
        return [l]
    return [p[:i]+[l[0]]+p[i:] for i in xrange(sz) for p in perm(l[1:])]


def geometric_dist(lower, upper, n):
    """Return 'n' numbers distributed geometrically between
    lower and upper.
    """
    const = 1.0/float(n-1.0)*np.log(float(upper)/float(lower))
    temps = np.zeros(n,dtype=float)
    for i in xrange(n): temps[i] = lower*np.exp(i*const)

    return temps


def nball_random_surface_point(ndims, radius=1.):
    """
    Uniformly randomly generate a point on the surface of the
    n-ball.

    """
    x = np.random.randn(ndims)
    r = np.sqrt((x**2.).sum())
    s = 1./r * x

    return radius * s


def fit(x, # array of x-values
        y, # array of y-values
        function,  # f(x, params) -> y
        initial, # numpy array of initial guess
        **leastsq_args):
    """Simple automatic fit function

    x           - vector of x-values
    y           - vector of y-values
    function    - function to be called as
                  function(x_vector, params) -> returns vector (shape y_vector)
    initial     - initial guess for fit.  The number of paramaters is taken
                  from the length of this vector.
    weights     - a vector, same dimensions the y_vector, if given, weight
                  the deviances from the y_vector by this.
    **kwargs    - other arguments to scipy.optimize.leastsq

    Sample:

    >>> x = numpy.array((0, 1, 2, 3, 4))
    >>> y = numpy.array((4, 1, 0, 1, 4))
    >>> function = lambda x, params: params[0] + params[1]*x + params[2]*x**2
    >>> initial = (0, 0, 0)
    >>> fit(x, y, function, initial)
    array([ 3.9999733 , -3.99996282,  0.9999921 ])
    """
    import scipy.optimize
    def optimizeFunc(params):
        new = function(x, params)
        errors = new - y
        return errors
    xopt, cov_x, infodict, mesg, errflag = \
          scipy.optimize.leastsq(optimizeFunc, initial,
                                 full_output=True, **leastsq_args)
    #print cov_x
    return xopt


def fit_simplex(x, # array of x-values
        y, # array of y-values
        function,  # f(x, params) -> y
        initial, # numpy array of initial guess
        weights=None,
        **fmin_args):
    """Simple automatic fit function

    x           - vector of x-values
    y           - vector of y-values
    function    - function to be called as
                  function(x_vector, params) -> returns vector (shape y_vector)
    initial     - initial guess for fit.  The number of paramaters is taken
                  from the length of this vector.
    weights     - a vector, same dimensions the y_vector, if given, weight
                  the deviances from the y_vector by this.
    **fmin_args - other arguments to scipy.optimize.fmin

    Sample:

    >>> x = numpy.array((0, 1, 2, 3, 4))
    >>> y = numpy.array((4, 1, 0, 1, 4))
    >>> function = lambda x, params: params[0] + params[1]*x + params[2]*x**2
    >>> initial = (0, 0, 0)
    >>> fit(x, y, function, initial)
    array([ 3.9999733 , -3.99996282,  0.9999921 ])
    >>> fit(x, y, function, initial, xtol=1e-10)
    array([ 4., -4.,  1.])
    """
    import scipy.optimize
    if weights:
        def optimizeFunc(params):
            new = function(x, params)
            error = (y - new)**2
            error = numpy.sum(error*weights)
            return error
    else:
        def optimizeFunc(params):
            new = function(x, params)
            error = (y - new)**2
            error = numpy.sum(error)
            return error
    xopt = scipy.optimize.fmin(optimizeFunc, initial,
                               disp=False,
                               **fmin_args
                               )
    return xopt


def polyfitw(x, y, w, ndegree, return_fit=0):
   """
   Performs a weighted least-squares polynomial fit with optional error estimates.

   Inputs:
      x:
         The independent variable vector.

      y:
         The dependent variable vector.  This vector should be the same
         length as X.

      w:
         The vector of weights.  This vector should be same length as
         X and Y.

      ndegree:
         The degree of polynomial to fit.

   Outputs:
      If return_fit==0 (the default) then polyfitw returns only C, a vector of 
      coefficients of length ndegree+1.
      If return_fit!=0 then polyfitw returns a tuple (c, yfit, yband, sigma, a)
         yfit:
            The vector of calculated Y's.  Has an error of + or - Yband.

         yband:
            Error estimate for each point = 1 sigma.

         sigma:
            The standard deviation in Y units.

         a:
            Correlation matrix of the coefficients.

   Written by:   George Lawrence, LASP, University of Colorado,
                 December, 1981 in IDL.
                 Weights added, April, 1987,  G. Lawrence
                 Fixed bug with checking number of params, November, 1998,
                 Mark Rivers.
                 Python version, May 2002, Mark Rivers
                 NumPy update, February 2010, John R. Dowdle
   """
   n = min(len(x), len(y))               # size = smaller of x,y
   m = ndegree + 1                       # number of elements in coeff vector
   a = np.zeros((m,m))                   # least square matrix, weighted matrix
   b = np.zeros(m)                       # will contain sum w*y*x^j
   z = np.ones(n)                        # basis vector for constant term

   a[0,0] = np.sum(w)
   b[0] = np.sum(w*y)

   for p in xrange(1, 2*ndegree+1):         # power loop
      z = z*x                               # z is now x^p
      if (p < m):  b[p] = np.sum(w*y*z)     # b is sum w*y*x^j
      wzsum = np.sum(w*z)
      for j in xrange(max(0,(p-ndegree)), min(ndegree,p)+1):
         a[j,p-j] = wzsum

   a = np.linalg.inv(a)
   c = np.dot(b, a)
   if (return_fit == 0):                 # exit if only fit coefficients are wanted
      return c[::-1]                     # reverse c to correspond to numpy's polyfit

   # compute optional output parameters.
   yfit = np.zeros(n)+c[0]               # one-sigma error estimates, init
   for k in xrange(1, ndegree +1):
      yfit = yfit + c[k]*(x**k)          # sum basis vectors
   var = np.sum((yfit-y)**2 )/(n-m)      # variance estimate, unbiased
   sigma = np.sqrt(var)
   yband = np.zeros(n) + a[0,0]
   z = np.ones(n)
   for p in xrange(1,2*ndegree+1):           # compute correlated error estimates on y
      z = z*x		                     # z is now x^p
      asum = 0.
      for j in xrange(max(0, (p - ndegree)), min(ndegree, p)+1):
         asum += + a[j,p-j]
      yband = yband + asum * z               # add in all the error sources
   yband = yband*var
   yband = np.sqrt(yband)
   return c[::-1], yfit, yband, sigma, a


def linear_leastsq(x, y, full_output=False):
    """find least-squares fit to y = ax + b

    inputs:
        x            sequence of independent variable data
        y            sequence of dependent variable data
        full_output  (optional) return dictionary of all results and stats

    outputs (not using full_output):
        a      coeffecient (slope) of regression line
        b      y intercept of regression line

    full output (using full_output):
        stats  dictionary containing statistics on fit
            key   value
            ---   -----------------------
            a     a in: y = ax + b
            b     a in: y = ax + b
            ap    a' in: x = b' + a'y
            bp    b' in: x = b' + a'y
            r2    correlation coeffecient
            var_x variance of x (sigma**2)
            var_y variance of y (sigma**2)
            cov   covariance
            SEa   standard error for a
            SEb   standard error for b
    """
    # see
    # http://mathworld.wolfram.com/CorrelationCoefficient.html
    # and http://mathworld.wolfram.com/LeastSquaresFitting.html

    x = np.asarray(x)
    y = np.asarray(y)
    n = len(x)
    assert n == len(y)
    mean_x = np.sum(x.astype(np.float64))/n
    mean_y = np.sum(y.astype(np.float64))/n

    SSxx = np.sum( (x-mean_x)**2 )
    SSyy = np.sum( (y-mean_y)**2 )
    SSxy = np.sum( x*y ) - n*mean_x*mean_y

    # y = b + a x
    # x = bp + ap y

    a = SSxy/SSxx
    ap = SSxy/SSyy

    b = mean_y - a*mean_x

    if not full_output:
        return a, b

    bp = mean_x - ap*mean_y

    s2 = (SSyy - a*SSxy)/(n-2)
    s = math.sqrt(s2)

    SEb = s*math.sqrt( 1/n + mean_x**2/SSxx )
    SEa = s/math.sqrt(SSxx)

    stats = dict(
        r2 = a*ap,      # correlation coefficient
        var_x = SSxx/n, # variance of x (sigma**2)
        var_y = SSyy/n, # variance of y (sigma**2)
        cov = SSxy/n,   # covariance
        SEa = SEa,      # standard error for a
        SEb = SEb,      # standard error for b
        a = a,          # a in: y = ax + b
        b = b,          # b in: y = ax + b
        ap = ap,        # a' in: x = b' + a'y
        bp = bp,        # b' in: x = b' + a'y
        )

    return stats

def extrema(input, halfwidth=2, excludeedges=False):
    """Find local extrema

    halfwidth: 


    Returns two lists (minima, maxima)
    """
    from scipy.ndimage.filters import generic_filter
    from scipy.ndimage import extrema
    """Return all local maxima/minima."""
    minima = collections.defaultdict(int)
    maxima = collections.defaultdict(int)
    inputLength = len(input)-1
    #i = [ 0 ]
    def f(array, il):
        i = il[0]
        # This function returns (mini, maxi), the indexes of the max
        # and min of the array.  They return the *lowest* possible
        # such indexes, thus the max(0, ...) below.
        min_, max_, mini, maxi = extrema(array)
        #print array, (min_, max_, mini, maxi), mini[0]+i-halfwidth, maxi[0]+i-halfwidth
        minima[max(0, mini[0]+i-halfwidth)] += 1
        maxima[       maxi[0]+i-halfwidth ] += 1
        il[0] += 1
        return 0
    #from fitz import interactnow
    generic_filter(input, f, size=2*halfwidth+1, mode='nearest',
                   extra_arguments=([0],) )
    if excludeedges:
        minima.pop(0, None) ; minima.pop(len(input)-1, None)
        maxima.pop(0, None) ; maxima.pop(len(input)-1, None)
    return list(sorted(k for k,v in minima.items() if v > (halfwidth))), \
           list(sorted(k for k,v in maxima.items() if v > (halfwidth)))

def _extrema_test():
    pass


if __name__ == "__main__":
    x = numpy.array((0, 1, 2, 3, 4))
    y = numpy.array((4, 1, 0, 1, 4))
    function = lambda x, params: params[0] + params[1]*x + params[2]*x**2
    initial = (4, -4, 1)
    print fit(x, y, function, initial)

    _test_Averager()
