# Richard Darst, Nomember 2011

"""
"""

import inspect
import pdb
import sys

def excepthookpdb(t, value, tb):
    """Exception hook to invoke pdb on exceptions."""
    sys.__excepthook__(t, value, tb)
    pdb.post_mortem(tb)
def enable():
    """Enable exception hook."""
    sys.excepthook = excepthookpdb
def disable():
    """Disable exception hook."""
    sys.excepthook = sys.__excepthook__

def run(func, *args, **kwargs):
    """Run a function with pdb exception hook enabled."""
    enable()
    func(*args, **kwargs)

def run_ipython(func, *args, **kwargs):
    """ipython pdb hook: invokes pdb on exceptions in ipython.

    The function func is called, with arguments args and
    kwargs=kwargs.  If this func raises an exception, pdb is invoked
    on that frame.  Upon exit from pdb, return to ipython normally."""
    try:
        func(*args, **kwargs)
    except Exception as e:
        #t, value, tb = sys.exc_info()
        sys.__excepthook__(t, value, tb)
        frame = sys.exc_info()[2]
        #tb = e.tb_frame
        pdb.post_mortem(tb)
        del frame   # the docs warn to avoid circular references.

def now(frame=None, stackLevel=1):
    """Run pdb in the calling frame."""
    if frame is None:
        frame = inspect.stack()[stackLevel][0]
    p = pdb.Pdb()
    def do_quit(self, arg):
        sys.exit()
    p.do_quit = type(p.do_quit)(do_quit, p, pdb.Pdb)
    p.do_q = p.do_quit
    p.reset()
    p.interaction(frame, None)


if __name__ == "__main__":
    import fitz.runpy2
    enable()
    fitz.runpy2.main()
