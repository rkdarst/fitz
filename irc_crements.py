#!/usr/bin/env python
# Richard Darst, June 2011

import collections
import datetime
import re
import sys

from irclogparser import LogParser

r = re.compile(r'([a-z1-9][a-z1-9-]{2,}) ?(\+\+|--)', re.I)
def count(iterable, value):
    return len([x for x in iterable if x==value])


allnicks = set()
crements = collections.defaultdict(list)
crementers = collections.defaultdict(list)

fname = sys.argv[1]
for message, nick, line, LP in LogParser(open(fname)):
    # skip early dates
    if LP.time < datetime.datetime(2011,1,1): continue
    # skip non-messages
    if message != "msg": continue
    sayerNick = nick.lower()
    allnicks |= set((sayerNick, ))
    m = r.search(line)
    if not m: continue
    nick, crementString = m.groups()
    nick = nick.lower()
    print sayerNick, nick, crementString
    if nick == sayerNick: continue
    if crementString == "++":
        crement = +1
    elif crementString == "--":
        crement = -1
    else:
        raise Exception("unknown crement")
    crements[nick].append(crement)
    crementers[sayerNick].append(nick)

for nick, crements in sorted(crements.iteritems(), key=lambda (k,v): sum(v), reverse=True):
    #if nick not in allnicks: continue
    print "%3d -%3d =%3d  %s"%(count(crements, 1), count(crements, -1), sum(crements), nick)

#for nick in crementers:
#    crementers[nick] = [x for x in crementers[nick] if x in allnicks]
for nick, crements in sorted(crementers.iteritems(), key=lambda (k,v): len(v), reverse=True):
    print "%3d  %s"%(len(crements), nick)
