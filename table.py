# Richard Darst, 2013 April

import collections
import sys

class TablePrinter(object):
    def __init__(self):
        self.widths = collections.defaultdict(int)
    def __call__(self, args, fout=sys.stdout):
        for i, arg in enumerate(args):
            arg = str(arg)
            self.widths[i] = max(self.widths[i], len(arg))
            print >> fout, arg.ljust(self.widths[i]),
        print >> fout
