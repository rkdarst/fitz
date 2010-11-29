# Richard Darst, May 2009
# David M. Creswick, Sept 2009

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


if __name__ == "__main__":
    x = numpy.array((0, 1, 2, 3, 4))
    y = numpy.array((4, 1, 0, 1, 4))
    function = lambda x, params: params[0] + params[1]*x + params[2]*x**2
    initial = (4, -4, 1)
    print fit(x, y, function, initial)

