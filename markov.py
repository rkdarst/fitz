# Richard Darst, June 2009

from fitz import irclogparser
import random
import re
import string
import sys

validChars = string.ascii_letters + string.digits
reInalidChars = re.compile("[^"+validChars+"]+")
reValidChars = re.compile("["+validChars+"]+")
reAllValidChars = re.compile("["+validChars+"]+$")
#def sanitize_word(word):
#    if len(word) > 15:
#        return ''
#    if reAllValidChars.match(word):
#        return word
#    return ''
def sanitize_word(word):
    return word

def sanitize_word(word):
    #words = reInvalidChars.split(word)
    #newword = ''
    #for w in words
    return reInalidChars.sub('', word)


debug = False

commonWords = set('''to the it that a is and of in do be have for
so are but on was like if or they would not with at as well more
with not dont'''.split())
commonWords = set(('',))

class Person(object):
    #recentWords = ('', '')
    #recentWords = '\0\0\0\0\0'
    #split_func = lambda self, x: (y for y in x)
    #join_char = ""
    def __init__(self, nick, mode='words', memory=1):
        self.nick = nick
        self.wordCounts = { }
        self.markovArray = { }
        if mode == 'words':
            self.split_func = re.compile(r'\s+').split
            self.join_char = " "
            self.recentWords = ('', ) * memory
        else:
            self.recentWords = '\0' * memory
            self.split_func = lambda self, x: (y for y in x)
            self.join_char = ""
            
    def __iadd__(self, (line, ) ):
        recentWords = self.recentWords
        if len(line) < 15 or 'http://' in line or 'UghBot' in line:
            return self
        for word in self.split_func(line):
            word = sanitize_word(word)
            if word == '':
                continue
            word = word.lower()
            # simple word counts
            self.wordCounts.setdefault(word, 0)
            self.wordCounts[word] += 1
            # markov chain:
            #if recentWords not in self.markovArray:
            #    self.markovArray[recentWords] = { }
            #self.markovArray.setdefault(recentWords, {})
            #self.markovArray[recentWords].setdefault(word, 0)
            self.markovArray.setdefault(recentWords, {}).setdefault(word, 0)
            #self.markovArray[recentWords]
            self.markovArray[recentWords][word] += 1
            #print self.markovArray
            # update recent words
            recentWords = recentWords[1:] + (word, )
            #recentWords = recentWords[1:] + word
            #recentWords = recentWords[1:] + (hash(word), )
        # End of line.
        word = ''
        self.markovArray.setdefault(recentWords, {}).setdefault(word, 0)
        self.markovArray[recentWords][word] += 1


    def topWords(self):
        topWords = sorted(((c,w) for w,c in self.wordCounts.iteritems()),
                          reverse=True)
        topWords = [(w,c) for c,w in topWords if w not in commonWords]

        return topWords

    def genSentence(self, length=10, counts=False, debugsent=None):
        markovArray = self.markovArray
        sentence = [ ]
        debugsentence = [ ]
        recentWords = self.recentWords
        #recentWords = (hash(''), hash(''))
        while True:
            if debug:
                print recentWords, len(markovArray.get(recentWords, ()))
            countdata = ""
            if recentWords in markovArray:
                selection = markovArray[recentWords]
            #elif ('',) + recentWords[1:] in markovArray:
            ##elif (hash(''),) + recentWords[1:] in markovArray:
            #    if debug:
            #        print "    not found:", recentWords
            #        print "    going to:", ('',) + recentWords[1:]
            #    countdata += '(1)'
            #    selection = markovArray[('',) + recentWords[1:]]
            #    #selection = markovArray[(hash(''),) + recentWords[1:]]
            ##elif ('',) + recentWords[:-1] in markovArray:
            ##    print "not found:", recentWords
            ##    selection = markovArray[('',) + recentWords[1:]]
            #else:
            #    if debug:
            #        print '    restarting, not found:', recentWords
            #        print '    going to:', ('', '')
            #    countdata += '(r)'
            #    selection = markovArray[('', '')]
            #    #selection = markovArray[(hash(''), hash(''))]
            totalNumber = sum(value for value in selection.itervalues())
            #print "  totalNumber", totalNumber
            choice = random.uniform(0, totalNumber)
            countdata += "(%d/%d)"%(len(selection), totalNumber)
            for w, c in selection.iteritems():
                choice -= c
                if choice <= 0:
                    next = w
                    break
            sentence.append(next)
            debugsentence.append(next+countdata)
            recentWords = recentWords[1:] + (next, )
            #recentWords = recentWords[1:] + next
            #recentWords = recentWords[1:] + (hash(next), )

            if length:
                length -= 1
                if length == 0:
                    break
            else:
                if next == '':
                    break
                
        if counts:
            debugsent.append(self.join_char.join(debugsentence))
        return self.join_char.join(sentence)
        #return self.join_char.join(debugsentence)
            #raise None

import collections
lines = collections.defaultdict(int)


def loadChannel(f, nicks=None, storage=None):
    parser = irclogparser.LogParser(f)

    if storage is None:
        AllNicks = { }
    else:
        AllNicks = storage
    for msgtype, nick, line, parser in parser:
        #if parser.totallines > 10000: break
        if msgtype not in ('msg', ):
            continue
        if nick[-1] == '_':
            nick = nick[:-1]
        lowernick = nick.lower()

        lines[sanitize_word(line.lower())] += 1
        #continue

        if nicks and lowernick not in nicks:
            continue
        if lowernick not in AllNicks:
            #AllNicks[nick] = {'wordCounts':{},
            #                  'markovArray':{}}
            AllNicks[lowernick] = Person(nick)
        NickData = AllNicks[lowernick]
        NickData += (line, )
        #line = line.split()
        #for word in line:
        #    word = sanitize_word(word)
        #    NickData['wordCounts'].setdefault(word, 0)
        #    NickData['wordCounts'][word] += 1
    return AllNicks

def printTopWords(people, number=None):
    topWords = [person.topWords() for person in people]
    maxlen = max(len(x) for x in topWords)
    print ("%-15s "*len(people))%tuple(p.nick for p in people)
    row_i = -1
    while True:
        row_i += 1
        for person_i in range(len(people)):
            top = topWords[person_i]
            if len(top) > row_i:
                print "%5d:%-9s"%(top[row_i][1], top[row_i][0]),
            else:
                print " "*15,
        print
        if number and row_i >= number:
            break
        if row_i >= maxlen:
            break

def topDigraphs(person):
     x = sorted(
         [ (sum([count for next,count in nextarray.iteritems()]), recent)
           for (recent, nextarray) in person.markovArray.iteritems()
                 if recent[0] != ''])


if __name__ == "__main__":
    #debug = True
    AllNicks = loadChannel(open(sys.argv[1]))
    #allsent = [ ]
    #for i in range(20):
    #    allsent.append(AllNicks['mrbeige'].genSentence(length=None))
    #for s in allsent:
    #    print s

    if False:
        printTopWords((AllNicks['mrbeige'],
                       AllNicks['mrmauve'],
                       AllNicks['mrblonde'],
                       AllNicks['mrcyan'],
                       AllNicks['mssnowflake'],
                       AllNicks['hydroxide'],
                       ), number=5000)
    if False:
        items = sorted(((v,k) for k,v in lines.iteritems() if v>1),
                          reverse=True)
        print "total lines duplicated:", sum(v for v,k in items)
        print "total lines duplicated > 10:", sum(v for v,k in items if v>10)
        print "total lines duplicated > 100:", sum(v for v,k in items if v>100)
        print "unique duplicated lines:", len(items)
        print "lines total:", sum(v for k,v in lines.iteritems())
        print
        for v,k in items:
            print "%3d"%v, k

    if True:
        nick = sys.argv[2]
        for i in range(1000):
            print AllNicks[nick].genSentence(length=15)

#printTopWords((AllNicks['MrBeige'],
#               AllNicks['Hydroxide'],
#               AllNicks['moray'],
#               AllNicks['h01ger'],
#               AllNicks['marga'],
#              ), number=None)
