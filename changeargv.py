# Richard Darst, June 2012

import ctypes
import os

f = ctypes.CDLL(os.path.join(os.path.dirname(__file)), '_changeargv.so')
