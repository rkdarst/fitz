# Richard Darst, June 2009

import datetime
import re
import sys

reLogOpen = re.compile('--- Log opened (?P<time>.*)')
reDateChanged = re.compile('--- Day changed (?P<time>.*)')
reMsg = re.compile('(?P<time>[^ ]+) <[@+ ]?(?P<nick>[^>:]*)(?::[^>]+)?> (?P<line>.*)')
reAction = re.compile('(?P<time>[^ ]+)  \* (?P<nick>[^ :]*)(?::[^ ]+)? (?P<line>.*)')
reTopic = re.compile('(?P<time>[^ ]+) -!- (?P<nick>[^ ]*) changed the topic of #[^ ]+ to: (?P<line>.*)')
# Record actions here which
ignoreREs = (re.compile('--- Log closed (?P<time>.*)'),
             re.compile('.* -!- .* has quit \[.*\]'),
             re.compile('.* -!- .* has left .* \[.*\]'),
             re.compile('.* -!- .* has joined'),
             re.compile('.* -!- Irssi:'),
             #re.compile('.* -!- Irssi: Join to'),
             #re.compile('.* -!- Irssi: You are now talking in'),
             re.compile('.* -!- .* is now known as .*'),
             re.compile('.* -!- Netsplit'),
             re.compile('.* -!- mode/.* by'),
             re.compile('.* -!- Keepnick:'),
             #re.compile('.* -!- .* has quit \[.*\]'),
             )

class LogParser(object):
    def __init__(self, f, assertOnErrors=False):
        self.f = f
        self.totallines = 0
        self.msglines = 0
        self.actionlines = 0
        self.topiclines = 0
        self._assertOnErrors = assertOnErrors

    def __iter__(self):
        """

        (msg, nick, line, self)

        <msg> = string indicating message type.  Currently parsed
                types are 'msg', 'action', 'topic'
        """
        for line in self.f:
            self.totallines += 1
            m = reLogOpen.match(line)
            if m:
                t = datetime.datetime.strptime(m.group('time'),
                                               '%a %b %d %H:%M:%S %Y')
                currentDate = t.replace(second=0)
                continue
            m = reDateChanged.match(line)
            if m:
                t = datetime.datetime.strptime(m.group('time'),
                                               '%a %b %d %Y')
                currentDate = t
                continue
            m = reMsg.match(line)
            if m:
                self.msglines += 1
                g = m.groupdict()
                hour, minute = g['time'].split(':')
                hour = int(hour) ; minute = int(minute)
                self.time = currentDate.replace(hour=hour, minute=minute)
                yield "msg", g['nick'], g['line'], self
                continue
            m = reAction.match(line)
            if m:
                self.actionlines += 1
                g = m.groupdict()
                hour, minute = g['time'].split(':')
                hour = int(hour) ; minute = int(minute)
                self.time = currentDate.replace(hour=hour, minute=minute)
                yield "action", g['nick'], g['line'], self
                continue
            m = reTopic.match(line)
            if m:
                self.topiclines += 1
                g = m.groupdict()
                hour, minute = g['time'].split(':')
                hour = int(hour) ; minute = int(minute)
                self.time = currentDate.replace(hour=hour, minute=minute)
                yield "topic", g['nick'], g['line'], self
                continue
            if self._assertOnErrors:
                for r in ignoreREs:
                    if r.match(line): break
                else:
                    print "Unmatched line:", line
                    assert False


if __name__ == "__main__":
    if sys.argv[1] == 'nickcount':
        files = sys.argv[2:]
        import collections
        nick_list = collections.defaultdict(int)
        for fname in files:
            parser = LogParser(open(fname))
            for msg, nick, line, LP in parser:
                nick_list[nick] += 1
        for k,v in sorted(nick_list.iteritems(), key=lambda x: x[1]):
            print k, v

    else:
        parser = LogParser(open(sys.argv[1]))
        for msg, nick, line, LP in parser:
            #print msg.upper(), nick, line
            pass

