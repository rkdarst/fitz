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

def run(func, *args, **kwargs):
    enable()
    func(*args, **kwargs)

def run_ipython(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        t, value, tb = sys.exc_info()
        sys.__excepthook__(t, value, tb)
        frame = sys.exc_info()[2]
        #tb = e.tb_frame
        pdb.post_mortem(tb)
        del frame


if __name__ == "__main__":
    import fitz.runpy2
    enable()
    fitz.runpy2.main()
