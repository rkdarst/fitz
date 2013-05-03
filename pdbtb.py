# Richard Darst, Nomember 2011

"""
"""

import pdb
import sys

def excepthookpdb(t, value, tb):
    sys.__excepthook__(t, value, tb)
    pdb.post_mortem(tb)
def enable():
    sys.excepthook = excepthookpdb
def disable():
    sys.excepthook = sys.__excepthook__

if __name__ == "__main__":
    import fitz.runpy2
    enable()
    fitz.runpy2.main()
