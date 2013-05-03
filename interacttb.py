# Richard Darst
"""Module to drop you into PDB after exceptions.

If you simply say 'import fitz.interacttb' in a script, it will
replace sys.excepthook with a function that will start pdb in the
current context at each traceback.
"""

import pdb
import sys
import traceback

from fitz import interact

def excepthook(t, value, tb):
    # Print the normal traceback.
    sys.__excepthook__(t, value, tb)
    while tb.tb_next is not None:
        tb = tb.tb_next
    #c_d = traceback.extract_tb(tb)
    #from fitz import interactnow
    interact.interact(frame=tb.tb_frame)
def excepthookpdb(t, value, tb):
    sys.__excepthook__(t, value, tb)
    pdb.post_mortem(tb)

#sys.excepthook = excepthook
sys.excepthook = excepthookpdb

def a():
    x = 1
    b()
    raise Exception("blah")
def b():
    y = 1
    raise Exception("blah2")

#a()
