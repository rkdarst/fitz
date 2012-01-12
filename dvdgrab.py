#!/usr/bin/env python
# Richard Darst, August 2011

"""
Good default config: crf=23.  You could do crf=22 for things you want better.


Example of command line usage:

python -m fitz.dvdgrab merge title="'The Seige'" dvddev="'THE_SEIGE.ISO'" track=6 audio='{130:"en",131:"fr"}' subtitles='{0:"en",2:"es", }' vf="pullup,softskip,crop=720:352:0:64,harddup" oggquality_aid="{131:-1}" aspect="'2.35'" xysize=720x352 crf=22

References:

Telecine:
- http://www.mplayerhq.hu/DOCS/HTML/en/menc-feat-telecine.html
- http://en.wikipedia.org/wiki/Telecine
- The best way to fix telecined or mixed telecined + progressive is:
  fps = '24000/1001'
  vf = 'pullup,softskip,harddup'

"""

from ast import literal_eval
import os
import cPickle as pickle
import logging
import re
import shlex
import shutil
import subprocess
from subprocess import Popen, call
import sys
import time

logger = logging.getLogger('dvdgrab')
logger.addHandler(logging.StreamHandler())
#logger.addHandler(logging.FileHandler('/dev/null'))
#import cStringIO
#logger.addHandler(logging.StreamHandler(cStringIO.StringIO())) # null

#cache_enabled = True

def var_eval(v):
    """Evaluate """
    try:
        v = literal_eval(v)
    except (SyntaxError, NameError, ValueError):
        pass
    return v

def listify(v):
    """Turn a string into a list, for use in options list."""
    if isinstance(v, str):
        # shlex returns a list.
        return shlex.split(v)
    return v

def asneeded(deps, prereqs=None):
    def _tmp(f):
        def new(*args, **kwargs):
            self = args[0]
            # Master cache flag
            if not getattr(self, 'cache', False):
                return f(*args, **kwargs)
            # Info on prereqs and mtimes
            deps2 = eval(deps, {'self': self})
            if prereqs is not None:
                prereqs2 = eval(prereqs, {'self': self})
            else:
                prereqs2 = ( )  # all(empty) = True
            # If either dependencies or prerequisites do not exist,
            # run it anyway.  We include prereqs here so the error
            # will be raised in the actual function, not here.
            if not (    all(os.access(fname, os.F_OK) for fname in deps2)
                    and all(os.access(fname, os.F_OK) for fname in prereqs2)):
                return f(*args, **kwargs)
            dep_mtimes    = [ os.stat(fname).st_mtime for fname in deps2 ]
            prereq_mtimes = [ os.stat(fname).st_mtime for fname in prereqs2 ]
            # if null prereqs, we'll never rerun.  Oly run if
            # dependencies don't exist (above).
            if prereqs and min(dep_mtimes) < max(prereq_mtimes):
                return f(*args, **kwargs)
            # If we get to this point, we are not re-running the function.
            return
        return new
    return _tmp


class Config(object):
    #f_basename - first key thing to override for full filename.
    title = ""         # Base of all filename configs
    extraname = ""     # Additional thing, like ".UTaH", for outputs and tmps.
    aspect = "4/3"     # like 4/3, 16/9, 2.35, 2.39.  Use "/"
    xysize = "720x480" # final size
    rescale = False
    detelecine = False
    fps = "24000/1001" # or "30000/1001".  Use "/"
    vbitrate = None    # Give only one of vbitrate, qp, crf, x264preset
    qp = None          # Give only one of vbitrate, qp, crf, x264preset
    crf = None         # Give only one of vbitrate, qp, crf, x264preset
                       # CRF - 0--51, 0=lossless
    x264preset = None  # Give only one of vbitrate, qp, crf, x264preset
                       # x264preset = ultrafast,veryfast,faster,fast,medium,
                       # slow,slower,veryslow,placebo
    passes = None      # override auto-detect number of passes.

    audio_rawrate = "48000" # ID_AUDIO_RATE=48000
    oggquality = 3
    oggquality_aid = { } # aid -> oggquality mapping
    audio =  { }       # example: {128:'en', }
    subtitles = { }    # example: {0:"en", 1:'es', 2:'fr', }
    cache = False      # Only regen files that are not there already.
    dry_run = False
    extravname = ""    # Extra tag to add on to temporary video filenames.

    # Program locations
    mplayer = "mplayer"
    mplayerid = "mplayer"
    mencoder = "mencoder"
    x264 = "x264"
    if os.uname()[1] == "ramanujan":
        mplayer = "/home/richard/sys/MPlayer-1.0rc1/mplayer"
        mencoder = "/home/richard/sys/MPlayer-1.0rc1/mencoder"
        x264 = "/home/richard/sys/x264/x264"
    if os.uname()[1] == "pyke":
        x264 = "/home/richard/sys/x264/x264"
    dvddev = "/dev/dvd"
    dvdmount = "/media/cdrom"
    tmp = "tmp."      # prefix for temporary files
    #tmp_fifo="/tmp"  # prefix for fifos (local filesystem)

    input = None  # overrides automatic input (.vob) file name
    vf = None  # String for mencoder video filter (for example, cropping)
    mencoderopts = [ "-cache", "16384" ]
    mplayeropts = [ ]  # only for do_source() type things
    threads = "auto"
    x264opts = [ "--tune=film", ]
    x264opts_pass1 = [ ]
    x264opts_pass2 = [ ]

class AutoConfig(object):

    fps = "24000/1001"
    vf = 'pullup,softskip,harddup'

    @property
    def aspect(self):
        aspect = self.iddict()['video_aspect']
        if   1.33  < aspect < 1.34:    return '4/3'
        elif 1.77  < aspect < 1.78:    return '16/9'
        elif 2.34  < aspect < 2.36:    return '2.35'
        elif 2.33  < aspect < 2.34:    return '21/9'
        elif 2.385 < aspect < 2.395:   return '2.39'
        else:
            raise Exception('Unknown auto-detected aspect radio: %s'%aspect)
    @property
    def xysize(self):
        x = self.iddict()['video_width']
        y = self.iddict()['video_height']
        return '%dx%d'%(x, y)
    @property
    def audio_rawrate(self):
        return self.iddict()['audio_rate']


class Film(Config, object):
    def __init__(self, title, **kwargs):
        self.title = title
        self.parseOptions(**kwargs)
        if hasattr(self, 'init_hook'):
            self.init_hook(**kwargs)
    def __getitem__(self, attrname):
        return getattr(self, attrname)
    def parseOptions(self, **kwargs):
        for key, value in kwargs.items():
            if key.endswith('_update') and hasattr(self, key[:-7]):
                key = key[:-7]
                setattr(self, key, getattr(self, key).copy())
                getattr(self, key).update(value)
            elif key.endswith('_append') and hasattr(self, key[:-7]):
                key = key[:-7]
                old = getattr(self, key)
                setattr(self, key, old + type(old)((value,)))
            elif not hasattr(self, key):
                raise Exception("kwargs can only set known attributes: %s"%
                                key)
            else:
                try:
                    setattr(self, key, value)
                except AttributeError:
                    # This is needed for attribute descriptors
                    # (@properties) which don't have a descriptor set.
                    # This is sort of a hack... what's the better way?
                    self.__dict__[key] = value
    @property
    def f_sourcename(self):       return self.title
    @property
    def f_basename(self):         return self.title+self.extraname
    @property
    def mkv_title(self):          return self.title
    @property
    def f_input(self):
        if self.input:    return self.input
        else:             return self.f_sourcename+".vob"
    @property
    def f_input_pickle(self):
        return self.f_input + '.idpickle'
    @property
    def f_chapters(self):         return self.f_sourcename+".chapters.txt"
    #@property
    #def f_sub_info(self):         return self.f_basename+".ifo"
    def f_sub(self, sid):         return self.tmp+self.f_basename+".subs.%d"%sid
    def f_subsub(self, sid):      return self.tmp+self.f_basename+".subs.%d.sub"%sid
    def f_subidx(self, sid):      return self.tmp+self.f_basename+".subs.%d.idx"%sid
    def f_audio_fifo(self, aid):  return self.tmp_fifo+self.f_basename+".audio.%d.fifo"%aid
    def f_audio_final(self, aid): return self.tmp+self.f_basename+".audio.%d.ogg"%aid
    #@property
    #def f_videobasename(self):
    #    return self.f_basename+".video"
    @property
    def f_x264log(self):          return self.tmp+self.f_videobasename+".video.x264.log"
    #def f_x264log(self):          return self.tmp+self.f_basename+".video.x264.log"
    @property
    def f_videobasename(self):
        return self.f_basename+(".video%s%s"%(self.qualitytag,self.extravname))
    @property
    def f_video_fifo(self):
        return self.tmp_fifo+self.f_videobasename+".fifo"
    @property
    def f_video_final(self):
        return self.tmp+self.f_videobasename+".mkv"
    @property
    def f_output(self):
        return self.f_basename+".mkv"
    #@property
    #def f_output(self):
    #    return self.f_basename+("%s.mkv"%self.qualitytag)
    @property
    def qualitytag(self):
        quality = ""
        if   self.crf:        quality = ".crf%s"%self.crf
        elif self.vbitrate:   quality = ".br%s"%self.vbitrate
        elif self.qp:         quality = ".qp%s"%self.qp
        #elif self.x264preset: quality = ".%s"%self.x264preset
        if self.x264preset:   quality = quality+".%s"%self.x264preset
        return quality

    @property
    def tmp_fifo(self):
        if 'tmp_fifo' in self.__dict__: return self.__dict__['tmp_fifo']
        else:
            return self.tmp

    def get_lsdvd(self):
        """Get lsdvd output from the original dvd.

        Return a dictionary representing the `lsdvd` utility
        information.

        There is one change to the output format.  The 'track' key is
        now the information about this track in specific, instead of
        about all tracks."""
        try:
            dat = pickle.load(open(self.f_input_pickle, 'rb'))
        except IOError:
            return None
        dat = dat['lsdvd']
        dat['track'] = dat['track'][0]
        return dat
    def get_identify(self, asdict=False):
        """Get mplayer -identify output from the original dvd.

        This is a list of (key, value) pairs, with all keys converted
        to lower case."""
        try:
            dat = pickle.load(open(self.f_input_pickle, 'rb'))
        except IOError:
            logger.warn("Not using pre-computed identify information")
            return self.do_iddict()
        dat = dat['mplayer']

        data = [ ]
        line_re = re.compile(r'ID_(\w+)=([^\n]*)')
        for line in dat:
            m = line_re.match(line.strip())
            if m:
                data.append((m.group(1).lower(), m.group(2).strip()))
        if asdict:
            data = dict(data)
        return data

    def detectaudio(self):
        """Automatically get audio data."""
        data = self.get_lsdvd()
        if data is None: return None
        audio = { }
        for a in data['track']['audio']:
            aid = literal_eval(a['streamid'])
            lang = a['langcode']
            audio[aid] = lang
        data = self.get_identify()
        for key,value in data:
            if key == 'audio_id':
                assert int(value) in audio \
                       or hasattr(self, '_overrideAudioErrors')
        #print audio, self.f_input
        return audio
    def detectsubtitles(self):
        """Automatically get subtitle data."""
        data = self.get_lsdvd()
        if data is None: return None
        subtitles = { }
        for i, s in enumerate(data['track']['subp']):
            sid = i  #literal_eval(s['streamid']) # count from zero instead
            lang = s['langcode']
            subtitles[sid] = lang
        data = self.get_identify()
        for key,value in data:
            if key == 'subtitle_id':
                assert int(value) in subtitles \
                       or hasattr(self, '_overrideSubErrors')
        return subtitles

    def do_checkconfig(self):
        data = self.do_idlist()

        audio = self.detectaudio()
        for key,value in data:
            if key == 'audio_id' and int(value) not in audio:
                print "Not found:", self.f_basename, 'audio:', value

        subtitles = self.detectsubtitles()
        for key,value in data:
            if key == 'subtitle_id' and int(value) not in subtitles:
                print "Not found:", self.f_basename, 'sub:', value
    def do_cropdetect(self):
        idd = self.get_identify(asdict=True)
        skip = 60
        if 'length' not in idd:
            print logger.warn('No length found for %s'%self.f_basename)

        if float(idd.get('length', 60)) < 60:
            skip = float(idd['length']) / 2
        cmd = [self.mplayer, '-benchmark', '-vo', 'null', '-nosound',
               '-msglevel', 'all=1:vfilter=6',
               '-ss', '%ss'%skip, '-frames', '1000',
               '-vf', 'cropdetect',
               self.f_input]
        #print cmd
        ps = Popen(cmd,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dat = ps.stdout.read()
        #print dat
        matches = tuple(re.finditer(r'-vf crop=((\d+):(\d+):(\d+):(\d+))',dat))
        #print matches
        if len(matches) == 0:
            print logger.warn('No cropdetect matches found for %s'%self.f_basename)
            return
        m = matches[-1]
        x = int(m.group(2))
        y = int(m.group(3))
        curx, cury = self.xysize.split('x')
        curx, cury = int(curx), int(cury)
        #print m.group(0), curx, cury
        if x < curx - 16 or y < cury - 16:
            print "%-30s"%self.f_basename[:30], m.group(1)


    def do_listcommands(self):
        return [ name[3:] for name in dir(self) if name.startswith('do_') ]

    def do_all(self):
        #self.source() # must call this yourself the first time
        self.do_subs()
        self.do_audio()
        self.do_video()
        self.do_merge()

    def do_source(self, track):
        pickle_data = { }

        # Set up the two mplayer commands: cmd_dump for -dumpstream,
        # cmd_identify for -identify
        cmd_base = [ self.mplayer, "dvd://%d"%track,
                     "-dvd-device", self.dvddev, ] + listify(self.mplayeropts)
        cmd_dump = cmd_base + ["-dumpstream", "-dumpfile", self.f_input ]
        cmd_identify = cmd_base +["-identify", "-msglevel", "identify=9:all=9",
                                  "-vo", "null", "-ao", "null",
                                  "-frames", "1",]
        cmd_identify[0] = self.mplayerid

        # Do mplayer -dumpstream and get the raw vob stream
        print cmd_dump
        if not self.dry_run:
            call(cmd_dump)

        # Grab output from mplayer -identify at this stage
        print cmd_identify
        if not self.dry_run:
            ps = Popen(cmd_identify,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            dat = ps.stdout.read()
            dat = dat.split('\n')
            dat = [ l for l in dat if l.startswith('ID_')
                                   or "VIDEO:" in l
                                   or "AUDIO:" in l ]
            pickle_data['mplayer'] = dat

        # Grab output from lsdvd at this page
        cmd_lsdvd = ["lsdvd", "-Oy", "-x", "-t", "%d"%track, self.dvddev ]
        print cmd_lsdvd
        if not self.dry_run:
            ps = Popen(cmd_lsdvd,
                       stdout=subprocess.PIPE)
            dat = ps.stdout.read()
            dat = dat.split('= ', 1)[1] # remove initial 'lsdvd = '
            dat = literal_eval(dat)
            pickle_data['lsdvd'] = dat

        if not self.dry_run:
            pickle.dump(pickle_data, open(self.f_input_pickle, 'wb'), -1)


        # Grap chapter data
        cmd = [ "dvdxchap", "-t", str(track), self.dvddev, ]
        print cmd
        fchap = open(self.f_chapters, 'w')
        if not self.dry_run:
            call(cmd, stdout=fchap)

        ## subtitle placement info
        #if os.access(self.f_sub_info, os.F_OK):
        #    call(('chmod', 'u+rw', self.f_sub_info))
        #shutil.copy(os.path.join(self.dvdmount,
        #                         ("VIDEO_TS/vts_%02d_0.ifo"%track).upper()),
        #            self.f_sub_info)
        #if os.access(self.f_sub_info, os.F_OK):
        #    call(('chmod', 'u+rw', self.f_sub_info))

    def do_identify(self, all=False, print_=True):
        """Information about the .vob file"""
        if print_:
            print "**** Information on:", self.f_input
        cmd = [self.mplayerid, "-identify", "-frames", "1",
               "-msglevel", "identify=9:all=9", "-vo", "null", "-ao", "null",
               self.f_input]
        logger.debug(repr(cmd))
        ps = Popen(cmd,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dat = ps.stdout.read()
        dat = dat.split('\n')
        if all == 'all':
            pass # include ALL the things.
        elif all:
            dat = [ l for l in dat if l.startswith("ID_")
                                   or "VIDEO:" in l
                                   or "AUDIO:" in l ]
        else:
            dat = [ l for l in dat if "AUDIO_ID" in l
                                   or "SUBTITLE_ID" in l
                                   or "VIDEO_ID" in l
                                   or "VIDEO:" in l
                                   or "VIDEO_ASPECT" in l
                                   or "LENGTH" in l]
            dat.sort() # not sort 'all'.
        if print_:
            print "\n".join(dat)
            print
        return dat
    def do_identifyall(self):
        self.do_identify(all=True)
    def do_identifyall2(self):
        self.do_identify(all='all')
    def do_iddict(self):
        """Return a dict of the identified portions."""
        if hasattr(self, '_iddict'):
            return self._iddict

        data = { }
        dat = self.do_identify(all=True, print_=False)
        line_re = re.compile(r'ID_(\w+)=([^\n]*)')
        for line in dat:
            m = line_re.match(line.strip())
            if m:
                data[m.group(1).lower()] = m.group(2).strip()
        self._iddict = data
        return self._iddict
    def do_idlist(self):
        """Return a dict of the identified portions."""
        if hasattr(self, '_idlist'):
            return self._idlist

        data = [ ]
        dat = self.do_identify(all=True, print_=False)
        line_re = re.compile(r'ID_(\w+)=([^\n]*)')
        for line in dat:
            m = line_re.match(line.strip())
            if m:
                data.append((m.group(1).lower(), m.group(2).strip()))
        self._idlist = data
        return self._idlist

    def do_detecttc(self):
        """Print out just the framerate changes.
        """
        print "**** Information on:", self.f_input
        cmd = [self.mplayerid, self.f_input,
               '-nosound', '-vo', 'null', '-benchmark']
        if not self.dry_run:
            call(cmd)

    def do_detectframerates(self):
        print "**** Information on:", self.f_input
        cmd = [self.mplayerid, self.f_input,
               '-nosound', '-vo', 'null', '-benchmark',
               '-msglevel', 'statusline=0']
        ps = Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dat = ps.stdout.read()
        #dat = dat.split('\n')
        dat = re.split(r'[\n\r]+', dat)
        dat = [l for l in dat if 'demux_mpg' in l]
        print '\n'.join(dat)
        return dat

    def do_showaudiosubs(self):
        audio = self.audio #detectaudio()
        subs = self.subtitles #detectsubtitles()
        print "%-30s"%self.f_input[:30], \
              "  ", ",".join("%s:%s"%x for x in sorted(audio.items())), \
              "  ", ",".join("%s:%s"%x for x in sorted(subs.items()))

    @asneeded('tuple(self.f_subsub(i) for i in self.subtitles.keys())'
              '+ tuple(self.f_subidx(i) for i in self.subtitles.keys())')
    def do_subs(self):
        print "**** Subtitles", self.subtitles
        # subtitles:
        for sid, lang in sorted(self.subtitles.items()):
            # We have to delete these files first.  It appends to
            # them, not overwrites them like other outputters do.
            for fname in (self.f_sub(sid), self.f_subsub(sid),
                          self.f_subidx(sid)):
                if os.access(fname, os.F_OK):
                    if not self.dry_run:
                        os.unlink(fname)
            # Do the dumping.
            cmd = [ self.mencoder, "-oac", "copy", "-ovc", "copy",
                    "-ofps", str(self.fps), "-o", "/dev/null",
                    "-sid", str(sid), "-vobsubout", self.f_sub(sid),
                    self.f_input, ]
            print cmd
            if not self.dry_run:
                call(cmd)


    @asneeded('(self.f_audio_final(i) for i in self.audio.keys())')
    def do_audio(self):
        #return
        for aid, lang in sorted(self.audio.items()):
            self._do_audio(aid)

    def _do_audio(self, aid):
        print "****Audio track", aid
        if not os.access(self.f_audio_fifo(aid), os.F_OK):
            os.mkfifo(self.f_audio_fifo(aid))
        # Run in background
        mencoder = [self.mencoder,
              "-ovc", "copy", "-vc", "dummy",
              "-aid", str(aid),
              "-ofps", str(self.fps),
              "-of", "rawaudio",
              "-oac", "pcm", "-af", "format=s16le",
#              "-vf", self.vf,
              "-o", self.f_audio_fifo(aid),
              self.f_input,
              ] + listify(self.mencoderopts)

        oggquality = self.oggquality
        if self.oggquality_aid and aid in self.oggquality_aid:
            oggquality = self.oggquality_aid[aid]
        # Run in foreground
        oggenc = ["oggenc",
              "-q"+str(oggquality),
              "--title", self.audio[aid],  # Could be made "English"
              "--quiet",
              "--raw-rate", str(self.audio_rawrate),
              "-o"+self.f_audio_final(aid),
              self.f_audio_fifo(aid),
              ]
        print mencoder
        print oggenc
        if not self.dry_run:
            Popen(mencoder)
            time.sleep(1)
            ret = call(oggenc)
            assert not ret, "Audio encoding failed: %s:%s"%(aid,self.audio[aid])
        os.unlink(self.f_audio_fifo(aid))


    @asneeded('(self.f_video_final, )')
    def do_video(self):
        print "****Video"
        if not os.access(self.f_video_fifo, os.F_OK):
            print self.f_video_fifo, self.tmp_fifo
            os.mkfifo(self.f_video_fifo)

        mencoder = [self.mencoder,
                    "-quiet", "-sid", "2999", # dummy sid to disable them.
                    "-oac", "copy", "-ovc", "raw", "-of", "rawvideo",
                    "-ofps", self.fps,
                    "-o", self.f_video_fifo,
                    #-vf crop=720:464:0:6,scale=704:384,dsize=-1,format=I420
                    self.f_input]
        # Create the video filter
        vf = [ ]
        if self.detelecine:
            vf.append('pullup,softskip,harddup')
        if self.vf:
            vf.extend(listify(self.vf))
        if self.rescale:
            vf.append('scale=%s'%(self.xysize.replace('x',':')))
        vf.append("dsize=-1,format=I420") # output encoding
        mencoder[1:1] = ["-vf", ",".join(vf)]
        # other options
        mencoder[1:1] = listify(self.mencoderopts)

        # check aspect for x264
        aspect = self.aspect
        aspect = aspect.replace("/", ":")
        if aspect.find(':') == -1:
            aspect = "1:"+aspect   # it should be w:h (?)
        x264 = [self.x264,
                #"--progress",
                #"--sar", aspect,
                "--stats", self.f_x264log,
                "--fps", self.fps,
                "--threads", str(self.threads),
                #"--psnr",
                #"--verbose",
                self.f_video_fifo]
        x264[1:1] = listify(self.x264opts)

        if getx264version(self.x264) >= '0.104':
            x264.extend(['--input-res', self.xysize])
        else:
            x264.extend([self.xysize])


        if self.vbitrate:
            x264[1:1] = ["--bitrate", str(self.vbitrate)]
        elif self.qp:
            x264[1:1] = ["--qp", str(self.qp)]
        elif self.crf:
            x264[1:1] = ["--crf", str(self.crf)]
        else:
            print "either key of 'vbitrate', 'qp', 'crf', or 'x264preset' should be specified."
            #sys.exit()

        if self.x264preset:
            x264[1:1] = ["--preset", str(self.x264preset)]

        # "crf" is a one-pass encoding.
        if not self.vbitrate and self.passes in (None, 1):
            x264[1:1] = ["-o", self.f_video_final]
            x264[1:1] = listify(self.x264opts_pass2)

            print "****Beginning only pass"
            print mencoder
            print x264
            if not self.dry_run:
                p1 = Popen(mencoder)
                time.sleep(1)
                call(x264)
                p1.wait()

        else:
            x264_pass1 = x264[:]
            x264_pass2 = x264[:]

            x264_pass1[1:1] = ["--pass", "1"]
            x264_pass1[1:1] = ["-o", "/dev/null"]
            x264_pass1[1:1] = listify(self.x264opts_pass1)

            x264_pass2[1:1] = ["--pass", "2"]
            x264_pass2[1:1] = ["-o", self.f_video_final]
            x264_pass2[1:1] = listify(self.x264opts_pass2)

            print "****Beginning pass 1"
            print mencoder
            print x264_pass1
            if not self.dry_run:
                p1 = Popen(mencoder)
                time.sleep(1)
                call(x264_pass1)
                p1.wait()

            print "****Beginning pass 2"
            print mencoder
            print x264_pass2
            if not self.dry_run:
                p2 = Popen(mencoder)
                time.sleep(1)
                call(x264_pass2)
                p2.wait()

        print "****Done with video encoding"
        os.unlink(self.f_video_fifo)


    #@asneeded('(self.f_final, )',
    #          '(self.f_audio_final(i) for i in self.audio.keys())'
    #          '+ (self.f_video_final)'
    #          )
    def do_merge(self):
        print "****Merging..."

        # Metadata part
        mkvmerge = ["mkvmerge",
                    "--default-duration", self.fps.replace("/",':')+'fps',
                    "--title",  self.title]
        if os.access(self.f_chapters, os.F_OK):
            mkvmerge.extend(("--chapters", self.f_chapters))
        # Video part
        if hasattr(self, "aspect"):
            mkvmerge.extend(["--aspect-ratio", '1:'+self.aspect])
        mkvmerge.extend(["--noaudio", self.f_video_final])

        # Audio
        for aid, lang in sorted(self.audio.items()):
            #a["audiofname"] = a["audiofname"]
            y = ["--novideo", self.f_audio_final(aid) ]
            #if a.has_key("language"):
            #    y[0:0] = ["--language", "0:"+a["language"]]
            y[0:0] = ["--language", "0:"+lang]
            mkvmerge.extend(y)

        # Subtitles
        for sid, lang in sorted(self.subtitles.items()):
            #mkvmerge.extend([ self.f_sub(sid) ])
            mkvmerge.extend(["--language", "0:"+lang, self.f_subidx(sid) ])

        # Merge it all
        mkvmerge.extend(["-o", self.f_output])
        print mkvmerge
        if not self.dry_run:
            call(mkvmerge)


class Episode(Film):
    """Part of a tv show.

    Defines 'seriestitle', 'season', and 'episode' as extra attributes."""
    #seriestitle = ""
    #season = 1

    def __init__(self, title,
                 seriestitle=None,
                 season=None, episode=None, **kwargs):
        if season:       self.season      = season
        if seriestitle:  self.seriestitle = seriestitle
        if episode:      self.episode     = episode
        super(Episode, self).__init__(title=title, **kwargs)

    @property
    def SxEid(self):
        try:
            return "%(season)dx%(episode)02d"%self
        except TypeError:
            return "%(season)sx%(episode)s"%self
    @property
    def f_sourcename(self):
        return "%(SxEid)s - %(title)s"%self
    @property
    def f_basename(self):
        return "%(SxEid)s - %(title)s%(extraname)s"%self
    @property
    def mkv_title(self):
        if self.seriestitle:
            return "%s %(SxEid)s - %s"%(self.seriestitle, self.SxEid, self.title)

def getx264version(cmd):
        ps = Popen([cmd, '--version'],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dat = ps.stdout.read()
        version = re.match(r'x264 (\S+)', dat).group(1)
        return version

def get_episode(episodes, s):
    if s == "*":
        for e in episodes:
            yield e
        return
    try:
        i = int(s)
        for e in episodes:
            if e.episode == i:
                yield e
    except ValueError:
        if "x" in s:  season, i = s.split('x')
        if "." in s:  season, i = s.split('.')
        try:
            i  = int(i)
        except ValueError:
            pass # leave i as string
        season = int(season)
        #print i, season
        for e in episodes:
            if e.season == season and (e.episode == i or i=="*"):
                yield e

def main_tvshow(episodes):
    from optparse import OptionParser
    parser = OptionParser(usage="[-h] [--track=N] command[,command,...] NxAA | Nx* [...] \n"
    "\n"
    "Valid commands: "+" ".join(episodes[0].do_listcommands()))
    parser.add_option("--track", "-t", type=int)
    parser.add_option("--config", "-c", type=str, action='append')
    parser.add_option("--loglevel", "-l", type=str, default='warn')
    (options, args) = parser.parse_args()

    logging.basicConfig(level=getattr(logging, options.loglevel.upper()))

    kwargs = { }
    if options.config:
        for opt in options.config:
            k, v = opt.split('=', 1)
            v = var_eval(v)
            kwargs[k] = v

    cmds = args[0].split(',')
    for s in args[1:]:
        for e in get_episode(episodes, s):
            e.parseOptions(**kwargs)

            for cmd in cmds:
                if cmd == "source":
                    e.do_source(track=options.track)
                else:
                    getattr(e, 'do_'+cmd)()


if __name__ == "__main__":
    args = sys.argv[1:]

    kwargs = { }
    commands = args[0].split(',')
    for arg in args[1:]:
        key, value = arg.split('=', 1)
        value = var_eval(value)
        if key == "track":
            track = value
            continue
        kwargs[key] = value
    f = Film(**kwargs)
    for cmd in commands:
        if cmd == "source":
            getattr(f, 'do_'+cmd)(track=track)
            continue
        getattr(f, 'do_'+cmd)()
