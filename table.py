# Richard Darst, 2013 April

import collections
import re
import sys
import time

class TablePrinter(object):
    def __init__(self):
        self.widths = collections.defaultdict(int)
    def __call__(self, args, fout=sys.stdout):
        for i, arg in enumerate(args):
            arg = str(arg)
            self.widths[i] = max(self.widths[i], len(arg))
            print >> fout, arg.ljust(self.widths[i]),
        print >> fout


def write_table(fobj, table, headers=[], labels=None):
    for line in headers:
        print >> fobj, "#", headerline
    print >> fobj, "#", time.ctime()
    print >> fobj, "#"+ " ".join("%d:%s"%(i+1,x) for i,x in enumerate(labels))

    for line in table:
        for x in line:
            print >> fobj, x,
        print >> fobj

def read_table(f, header=False):
    lines = [ ]
    headers = [ ]
    labels = None
    for line in f:
        if line.strip().startswith('#'):
            m = re.findall('(\d+):(\S+)', line)
            if m:  # m is a list of (group1, group2)
                indices, labels = zip(*m)
            continue
        if line.strip().startswith('#'):
            headers.append(line[1:].strip())
            continue
        line = line.split()
        line = [ float(x) for x in line ]
        lines.append(line)
    if header:
        return lines, headers, labels
    return lines


def transform_tables(transformations, *tables):
    """Input two tables, output transformation of them

    aN is first table, bN is second table, etc.
    a0 = 1st element in table 0, a1 = 2nd element in table 0, etc.

    Transformations is a comma-separated list of expressions to be
    python eval()'ed with the a0, a1, b0, b1, etc, variables defined.
    """
    transformations = transformations.split(',')
    newtable = [ ]
    import math
    math_vars = dict((k, v) for k,v in math.__dict__.iteritems()
                     if not k.startswith('_'))
    for rows in zip(*tables):
        newtable.append([])
        # Generate variables
        vars = math_vars.copy()
        for rowid, row in enumerate(rows):
            for colid, col in enumerate(row):
                vars["%s%d"%(string.lowercase[rowid], colid)] = col
        for t in transformations:
            newtable[-1].append(eval(t, vars))
    return newtable
