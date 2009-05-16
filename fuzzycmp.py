# Richard Darst, 2005

"""Comparison functions which accpet an uncertainty

I realized:
| 15:08 < MrBeige> I know how to look at it !
| 15:08 < MrBeige> there are two ways:
| 15:09 < MrBeige> a) when in doubt, the numbers are equal/not equal ...
| 15:09 < MrBeige> b) when in doubt, the compariason is True/False
| 15:09 < MrBeige> I guess that is really four ways

I take the option 'a with equal'.  When there is any doubt as to what
you should do, I assume that the numbers are equal.  

"""

# epsilon is defined so that two uncertain numbers which differ by
# exactly epsilon are equal.
epsilon = .0001

# Bug: you can't have different values of epsilon for different parts
# of your code.  To be truly elegant this must be fixed.


fuzzyeq  = lambda x, y: abs(x-y) <=  epsilon
fuzzyneq = lambda x, y: abs(x-y) >   epsilon
eq = fuzzyeq
neq = fuzzyneq

fuzzylt  = lambda x, y:     x-y  <  -epsilon
fuzzyleq = lambda x, y:     x-y  <=  epsilon
lt = fuzzylt
leq = fuzzyleq

fuzzygt  = lambda x, y:     x-y  >   epsilon
fuzzygeq = lambda x, y:     x-y  >=  -epsilon
gt = fuzzygt
geq = fuzzygeq

def fuzzyin(value, list, cmpfunc=fuzzyeq):
    """Return True if cmpfunction is True for value and any element in list.
    """
    for listvalue in list:
        if cmpfunc(value, listvalue):
            return True
    return False


if __name__ == "__main__":
    epsilon = .0001
    # insert test scripts here
    print "all test results should be True"

    print "* eq"
    print not fuzzyeq(1., 1.00011)
    print     fuzzyeq(1., 1.0001)
    print     fuzzyeq(1., 1.00005)
    print     fuzzyeq(1., 1.)
    print     fuzzyeq(1., 0.99995)
    print     fuzzyeq(1., 0.9999)
    print not fuzzyeq(1., 0.9998)
    print
    
    print "*neq"
    print     fuzzyneq(1., 1.00011)
    print not fuzzyneq(1., 1.0001)
    print not fuzzyneq(1., 1.00005)
    print not fuzzyneq(1., 1.)
    print not fuzzyneq(1., 0.99995)
    print not fuzzyneq(1., 0.9999)
    print     fuzzyneq(1., 0.9998)
    print
    
    print "* gt"
    print not fuzzygt(1., 1.00011)
    print not fuzzygt(1., 1.0001)
    print not fuzzygt(1., 1.00005)
    print not fuzzygt(1., 1.)
    print not fuzzygt(1., 0.99995)
    print not fuzzygt(1., 0.9999)
    print     fuzzygt(1., 0.9998)
    print

    print "* geq"
    print not fuzzygeq(1., 1.00011)
    print     fuzzygeq(1., 1.0001)
    print     fuzzygeq(1., 1.00005)
    print     fuzzygeq(1., 1.)
    print     fuzzygeq(1., 0.99995)
    print     fuzzygeq(1., 0.9999)
    print     fuzzygeq(1., 0.9998)
    print

    print "* lt"
    print     fuzzylt(1., 1.00011)
    print not fuzzylt(1., 1.0001)
    print not fuzzylt(1., 1.00005)
    print not fuzzylt(1., 1.)
    print not fuzzylt(1., 0.99995)
    print not fuzzylt(1., 0.9999)
    print not fuzzylt(1., 0.9998)
    print

    print "* leq"
    print     fuzzyleq(1., 1.00011)
    print     fuzzyleq(1., 1.0001)
    print     fuzzyleq(1., 1.00005)
    print     fuzzyleq(1., 1.)
    print     fuzzyleq(1., 0.99995)
    print     fuzzyleq(1., 0.9999)
    print not fuzzyleq(1., 0.9998)
    print

    
