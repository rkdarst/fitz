#!/usr/bin/env python

from __future__ import division

import cgitb
cgitb.enable()

import cgi
import glob
import os
import random
import re
import StringIO
import sys

class Holder:
    def _get_score1(self):
        try:
            return self.nwin / (self.nwin + self.nlose)
        except ZeroDivisionError:
            return 0.
    score1 = property(fget=_get_score1)


allowedchars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.'
def sanitize(string, chars=allowedchars):
    if string is None:
        return None
    return "".join([ x for x in string if x in chars ])

class Config(object):
    img_rexpc = re.compile(r".*\.jpg$")

data = cgi.FieldStorage()
page = sanitize(data.getfirst("p"))


class Voting(object):
    @property
    lambda : [ x for x in os.listdir(".") if self.img_rexpc.match(x) ]

if page == "v":

    vA = sanitize(data.getfirst("b"))
    vB = sanitize(data.getfirst("w"))
    if vA and vB:
        file("_rawvotes.txt", "a").write("%d %d\n"%(int(vA), int(vB)))
        print "303 Go back to voting:"
        print "Location: ?p=v"
        print "Content-Type: text/html"
        print
        print 'Thanks...'
        sys.exit(0)

    print "Content-Type: text/html"
    print
    
    print "voting!<br><br>"

    #print "don't vote yet, your votes will be lost!<p>"

    import cPickle as pickle
    top = pickle.load(file("_votedata.pickle"))
    sorted_score = top
    sorted_nvotes = [ (img.nvotes, img) for s, n, img in top ]
    sorted_nvotes.sort()

    #print sorted_score
    #print sorted_nvotes

    # pick an image
    rand = random.uniform(0, 1)
    if rand < .25:
        choicetype = "fewvotes"
        # do images that don't have many votes
        choices = sorted_nvotes[ : int(.1*len(sorted_nvotes))]
        choices = [ x[1].n for x in choices ]

    elif rand < .55:
        # do images that are near each other in score
        choicetype = "near"
        low = random.uniform(0, 1-.25)
        high = low + .25
        low =  int(low * len(imgs))
        high = int(high * len(imgs))
        choices = imgs[low:high]
    elif rand < .85:
        # do images that are near the top
        choicetype = "top"
        choices = sorted_score[ :int(.35*len(sorted_nvotes)) ]
        choices = [ x[2].n for x in choices ]
    else:
        choicetype = ""
        choices = imgs
        choices = imgs
        
    img1 = choices.pop(random.choice(range(len(choices))))
    img2 = choices.pop(random.choice(range(len(choices))))


    h1 = hash(img1)
    h2 = hash(img2)
    print 'click on the better image (%s):<p>'%choicetype
    print 
    print '<a href="?p=v&b=%(h1)s&w=%(h2)s"><img src=thumbnail/%(img1)s border=0></a> ' \
          '<a href="?p=v&b=%(h2)s&w=%(h1)s"><img src=thumbnail/%(img2)s border=0></a> <br><br>' \
          %locals()
    print '<a href="_vote.cgi">main vote page</a><br>'
    print '<a href="./">main lolcat page</a><br>'


elif page == "t" or (len(sys.argv)>1 and  sys.argv[1] == "record"):
    print "Content-Type: text/html"
    print
    print "voting!<br><br>"
    alg = int(sanitize(data.getfirst("alg", "0")))
    if len(sys.argv) > 1: alg = int(sys.argv[2])

    print '<a href="_vote.cgi">main vote page</a><br>'
    print '<a href="./">main lolcat page</a><br><p>'
    print 'using ranking algorithm:', alg, '<br>'
    print '<a href="?p=t&alg=0">algorithm 0</a> -- at xkcd ()<br>'
    print '<a href="?p=t&alg=1">algorithm 1</a> --  <br>'
    print '<a href="?p=t&alg=2">algorithm 2</a> --  <br>'
    print '<p>'
    imgs.sort()
    Imgs = [ Holder() for i in range(len(imgs)) ]
    for i, x in enumerate(imgs):
        Imgs[i].n = x
        Imgs[i].i = i
        Imgs[i].h = hash(x)
        Imgs[i].score = 1.
        Imgs[i].nwin = 0.
        Imgs[i].nlose = 0.
        
    indexHash = { }
    nameIndex = { }
    for x in Imgs:
        indexHash[x.h] = x.i
        nameIndex[x.i] = x.n
        
    #print Imgs, "<p><p><p>"

    #Nwinner = { }
    #Nloser = { }
    totvotes = 0

    #for i in range(len(Imgs)):
    #    Nwinner[i] =  0.
    #    Nloser[i] = 0.

    for line in file("_rawvotes.txt"):
        a, b = line.split()
        a = int(a) ; b = int(b)
        ia = indexHash[a]
        ib = indexHash[b]
        Ia = Imgs[ia]
        Ib = Imgs[ib]
        if alg == 0:
            Ia.nwin += 1
            Ib.nlose += 1
        if alg == 1:
            if Ia.score1 > Ib.score1:
                adj = .5
            elif Ia.score1 < Ib.score1:
                adj = 1.5
            else:
                adj = 1.
            Ia.nwin += adj
            Ib.nlose += adj
        if alg == 2:
            if Ia.score > Ib.score:
                adj = 0.
            elif Ia.score < Ib.score:
                adj = Ib.score - Ia.score
            else:
                adj = 1.
            Ia.score += adj
            Ib.score -= adj
            Ia.nwin += 1
            Ib.nlose += 1
            
        totvotes += 1

        #scoreadjust = abs(Imgs[ia] - Imgs[ib])
        
    top = [ ]
    for i, x in enumerate(Imgs):
        #try:
        #    score = x.nwin / (x.nwin + x.nlose)
        #except ZeroDivisionError:
        #    score = 0
        x.nvotes = x.nwin + x.nlose
        if alg in (0, 1):
            x.score = x.score1 #* x.nvotes / totvotes
        #x.score += 
        top.append((x.score, x.nvotes, x))

    if alg == 3:
        def findTop():
            pass
        for line in file("_rawvotes.txt"):
            a, b = line.split()
            a = int(a) ; b = int(b)
            ia = indexHash[a]
            ib = indexHash[b]
            Ia = Imgs[ia]
            Ib = Imgs[ib]
            if alg == 0:
                Ia.nwin += 1
                Ib.nlose += 1
            if alg == 1:
                if Ia.score1 > Ib.score1:
                    adj = .5
                elif Ia.score1 < Ib.score1:
                    adj = 1.5
                else:
                    adj = 1.
                Ia.nwin += adj
                Ib.nlose += adj
            if alg == 2:
                if Ia.score > Ib.score:
                    adj = 0.
                elif Ia.score < Ib.score:
                    adj = Ib.score - Ia.score
                else:
                    adj = 1.
                Ia.score += adj
                Ib.score -= adj
                Ia.nwin += 1
                Ib.nlose += 1
                
            totvotes += 1
    
            #scoreadjust = abs(Imgs[ia] - Imgs[ib])
            
        top = [ ]
        for i, x in enumerate(Imgs):
            #try:
            #    score = x.nwin / (x.nwin + x.nlose)
            #except ZeroDivisionError:
            #    score = 0
            x.nvotes = x.nwin + x.nlose
            if alg in (0, 1):
                x.score = x.score1 #* x.nvotes / totvotes
            #x.score += 
            top.append((x.score, x.nvotes, x))

    top.sort()
    top.reverse()
    #print top

    for _, _, x in top[:15]:
        print '<a href="%s"><img src="./thumbnail/%s"></a>'%(x.n, x.n)
        print "(%s, %s)"%(x.nwin, x.nlose)
        print '<p>'


    #print Imgs, '<p>'
    print '<a href="_vote.cgi">main vote page</a><br>'
    print '<a href="./">main lolcat page</a><br><p>'
    print '<table>'
    for i, (_, _, x) in enumerate(top):
        print '<tr><td>%d</td><td>'%i, '<a href="%s">%s</a>'%(x.n, x.n), '</td><td>', x.nwin, '</td><td>', x.nlose, '</td><td>', x.score,'</td></tr>' #<br>'
    print '</table>'

    import cPickle as pickle

    if len(sys.argv) > 1:
        pickle.dump(top, file("_votedata.pickle", "w"))

else:
    print "Content-Type: text/html"
    print
    print "voting!<br><br>"


    print '<a href="?p=v">voting</a><br>'
    print '<a href="?p=t">top images</a><br>'
    print '<p><p><p>'
    print """The algorithm I use right now is as described at
            http://bestthing.info/algorithms.html, which to me doesn't
            really seem that good unless everything has been voted on
            many times.  Thus, I need to find ways to strategically
            sample images to vote on, and/or find another method.
    """

