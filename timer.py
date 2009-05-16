# Richard Darst, 2006

"""Provides a stopwatch for code.

Classes
=======

There is a class defined called Timer.  It has the following methods:

__init__ -- argument is `clock`, which is the timing function to use
            for this timer.  It defaults to proctime.
reset -- zero the stopwatch.  The getrusage system call is zeroed when
         the code starts (and the timer keeps this zero initially),
         but calling reset() zeros it.  Zeroing is done by recording
         the current time and subtracting this out from future calls.
time -- returns the time since the last reset
lap -- return the time from the last reset, and reset it.

Global functions
================

t -- an automatically created instance of timer, using `proctime`.

start--  ~\   The methods on `t` are bound to the global namespace, 
time --    >  so timer.start(), etc, can be used if this what you 
reset--  _/   need.

The module includes various clock functions to use, such as
`realtime`, `proctime`, `usertime`, and `systime`.

"""

import resource
import time as timemodule

def systime():
    """Time spent executing system calls.

    Time spend doing things like disk access, IO, etc.

    Uses the system call getrusage().ru_stime
    """
    return resource.getrusage(resource.RUSAGE_SELF).ru_stime
def usertime():
    """Time spent executing code in user mode.

    Time spent doing things like adding numbers.

    Uses the system call getrusage().ru_utime
    """
    return resource.getrusage(resource.RUSAGE_SELF).ru_utime
def proctime():
    """Time spent by processor executing code

    sys + user time
    """
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime+r.ru_stime
def realtime():
    """Time on a clock on the wall.

    If your processor isn't busy doing other things, this will be the
    best to find how much time your code takes.

    time.time(), which uses the system call gettimeofday() for greater
    accuracy when avaliable.
    """
    return timemodule.time()

class Timer:
    _starttime = 0.
    def __init__(self, clock=proctime):
        """Create rusage object using a certain timing function.

        The argument `clock` is the clock function to use.  Default is
        proctime.
        """
        self._clock = clock
    def reset(self):
        """Reset the timer
        """
        self._starttime = self._clock()

    def time(self):
        """Return time since last reset
        """
        return self._clock() - self._starttime

    def lap(self):
        """Reset and return time since last reset
        """
        oldtime = self._clock() - self._starttime
        self._starttime = self._clock()
        return oldtime
    
t = Timer()
reset = t.reset
time = t.time
lap = t.lap
