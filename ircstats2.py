import re
import sys

from fitz.mathutil import Averager
class NickStats(object):
    def __init__(self):
        self.lines = 0
        self.allLines = 0
        self.chars = 0
        self.lastline = 0
        self.maxInARow = 0
        self.maxCharsInARow = 0
        self._lastInARow = 0
        self._lastCharsInARow = 0
        self.LineStats = Averager()
        self._lengthsList = [ ]
    def __iadd__(self, (lineno, line)):
        # how many lines in a row, on average?
        if lineno == self.lastline+1:
            self._lastInARow += 1
            self._lastCharsInARow += len(line)
        else:
            self.maxInARow = max(self.maxInARow, self._lastInARow)
            self.maxCharsInARow = max(self.maxCharsInARow, self._lastCharsInARow)
            self._lastInARow = 1
            self._lastCharsInARow = 1
        # count of all lines, even shourt ones:
        self.allLines += 1
        # filter which lines to consider
        if len(line) < 10: return self
        # basic stats
        self.LineStats.add(len(line))
        self.lines += 1
        self.chars += len(line)
        self._lengthsList.append(len(line))
        # record the last line we saw and continue
        self.lastline = lineno
        return self
    @property
    def longFrac(self):
        return float(self.lines) / self.allLines
    @property
    def mean(self):
        return self.LineStats.mean
    @property
    def std(self):
        return self.LineStats.std
    @property
    def median(self):
        if len(self._lengthsList) == 0: return float('nan')
        index = len(self._lengthsList)//2
        return sorted(self._lengthsList)[index]
    @property
    def skew(self):
        if self.std == 0: return float('nan')
        return 30*(self.mean - self.median)/self.std

nicks = { }

from fitz import irclogparser
parser = irclogparser.LogParser(open(sys.argv[1]))#open("#debconf-team.log"))

for msgtype, nick, line, parser in parser:
    #print parser.time
    if msgtype not in ('msg', 'action'):
        continue
    if nick not in nicks:
        nicks[nick] = NickStats()
    #print nicks[l['nick']]
    nicks[nick] += (parser.msglines+parser.actionlines, line)
    #nicks[l['nick']][1] += len(line)

    #if lineno > 500: break
nicks_sorted = reversed(sorted((nicks.iteritems()), key=lambda x:x[1].lines ))
print "totals:", sum( [v.lines for v in nicks.itervalues()] ), sum( [v.chars for v in nicks.itervalues()] )
print "%-15s %6s %7s %5s %5s %5s %4s %4s %3s %5s"%(
    'nick', 'lines', 'chars', '>10', 'mean', 'media', 'std', 'skew', 'rw', 'chrw')
for n,v in nicks_sorted:
   try:
    print "%-15s %6d %7d %5.2f %5.1f %5.1f %4.1f %4.1f %3d %5d"%(
        n, v.lines, v.chars, v.longFrac, v.mean, v.median, v.std, v.skew, v.maxInARow, v.maxCharsInARow)
   except IOError:
       sys.exit()
