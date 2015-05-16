import re
import sys

class Line(object):
    """One entry in a .srt file."""
    def __init__(self, i, ts, text):
        self.i = i
        self.ts = ts
        self.text = text

def open_srt(fname):
    """Open a .srt file and convert to list of Lines"""
    data = open(fname, 'U').read().decode('utf-8')
    print repr(data[-150:])
    srt_re = re.compile(ur"""(?:^|\ufeff) ([0-9]+)\n
                            ^([0-9:,\u060c.\s<>-]+)\n
                            (.+?)
                            (?: \n\s*\n | \s* \Z )
                            """, re.X|re.M|re.S)
    m = srt_re.findall(data)
    print m[-2:]
    return [Line(int(i), ts, text)
            for i, ts, text in m]

def check(srtlist):
    """Sanity-check for correct reading of files"""
    assert [S.i for S in srtlist] == range(1, len(srtlist)+1)

def mergesrt(s1, s2):
    """Move text of s2 onto s1"""
    new = [ ]
    for a, b in zip(s1, s2):
        assert a.i == b.i
        new.append(Line(i=a.i, ts=a.ts, text=b.text))
    return new

def savesrt(fname, srtlist):
    """Save list of SRT lines to a file"""
    f = open(fname, 'w')
    f.write(u'\ufeff'.encode('utf-8'))
    for line in srtlist:
        f.write(("%(i)d\n%(ts)s\n%(text)s\n\n"%line.__dict__).encode('utf-8') )

if __name__ == "__main__":
    orig = open_srt(sys.argv[1])
    check(orig)

    translated = open_srt(sys.argv[2])
    check(translated)

    new = mergesrt(orig, translated)
    savesrt(sys.argv[3], new)
