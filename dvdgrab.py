#!/usr/bin/env python
# Richard Darst, August 2011

"""

References:

Telecine:
- http://www.mplayerhq.hu/DOCS/HTML/en/menc-feat-telecine.html
- http://en.wikipedia.org/wiki/Telecine
- The best way to fix telecined or mixed telecined + progressive is:
  fps = '24000/1001'
  vf = 'pullup,softskip'

"""

import os
import shutil
import subprocess
from subprocess import Popen, call
import sys
import time

class Config(object):
    #f_basename - first key thing to override for full filename.
    #aspect = "2.35"   # like 4/3, 16/9, 2.35.  Use "/"
    xysize = "720x480" # final size
    fps = "24000/1001" # or "30000/1001".  Use "/"
    vbitrate = None    # Give only one of vbitrate, qp, crf, x264preset
    qp = None          # Give only one of vbitrate, qp, crf, x264preset
    crf = None         # Give only one of vbitrate, qp, crf, x264preset
                       # CRF - 0--51, 0=lossless
    x264preset = None  # Give only one of vbitrate, qp, crf, x264preset
    audio_rawrate = "48000" # ID_AUDIO_RATE=48000
    oggquality = 3
    oggquality_aid = { } # aid -> oggquality mapping

    mplayer = "/home/richard/sys/MPlayer-1.0rc1/mplayer"
    mplayerid = "mplayer"
    mencoder = "/home/richard/sys/MPlayer-1.0rc1/mencoder"
    if not os.access(mencoder, os.F_OK):  mencoder = "mencoder"
    x264 = "/home/richard/sys/x264/x264"
    dvddev = "/dev/dvd"
    dvdmount = "/media/cdrom"
    tmp = "tmp." # prefix for temporary files
    #tmp_filo="/tmp"  # Other

    input = None  # overrides automitic input (.vob) file name
    vf = None  # String for mencoder video filter (for example, cropping)
    groupid = ""
    mencoderopts = [ "-cache", "8092" ]
    threads = "auto"
    x264opts = [ "--tune=film", "--trellis=2", "--b-pyramid", "--bframes=4" ]
    x264opts_pass1 = [ ]
    x264opts_pass2 = [ ]


class Film(Config, object):
    def __init__(self, title, **kwargs):
        self.title = title
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise Exception("kwargs can only set known attributes")
            setattr(self, key, value)

    def __getitem__(self, attrname):
        return getattr(self, attrname)
    @property
    def f_basename(self):         return self.title+self.groupid
    @property
    def mkv_title(self):          return self.title
    @property
    def f_input(self):
        if self.input:    return self.input
        else:             return self.f_basename+".vob"
    @property
    def f_chapters(self):         return self.f_basename+".chapters.txt"
    #@property
    #def f_sub_info(self):         return self.f_basename+".ifo"
    @property
    def f_x264log(self):          return self.tmp+self.f_basename+".video.x264.log"
    def f_sub(self, sid):         return self.tmp+self.f_basename+".subs.%d"%sid
    def f_subsub(self, sid):      return self.tmp+self.f_basename+".subs.%d.sub"%sid
    def f_subidx(self, sid):      return self.tmp+self.f_basename+".subs.%d.idx"%sid
    def f_audio_fifo(self, aid):  return self.tmp_fifo+self.f_basename+".audio.%d.fifo"%aid
    def f_audio_final(self, aid): return self.tmp+self.f_basename+".audio.%d.ogg"%aid
    #@property
    #def f_videobasename(self):
    #    return self.f_basename+".video"
    @property
    def f_videobasename(self):
        return self.f_basename+(".video%s"%self.qualitytag)
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
        elif self.x264preset: quality = ".%s"%self.x264preset
        return quality

    @property
    def tmp_fifo(self):           return self.tmp

    def do_all(self):
        #self.source() # must call this yourself the first time
        self.do_subs()
        self.do_audio()
        self.do_video()
        self.do_merge()

    def do_source(self, track):
        # Get the raw vob stream
        cmd = [ self.mplayer, "dvd://%d"%track,
                "-dumpstream",
                "-dumpfile", self.f_input ]
        print cmd
        call(cmd)

        # get chapter data
        cmd = [ "dvdxchap", "-t", str(track), "/dev/dvd", ]
        fchap = open(self.f_chapters, 'w')
        call(cmd, stdout=fchap)

        ## subtitle placement info
        #if os.access(self.f_sub_info, os.F_OK):
        #    call(('chmod', 'u+rw', self.f_sub_info))
        #shutil.copy(os.path.join(self.dvdmount,
        #                         ("VIDEO_TS/vts_%02d_0.ifo"%track).upper()),
        #            self.f_sub_info)
        #if os.access(self.f_sub_info, os.F_OK):
        #    call(('chmod', 'u+rw', self.f_sub_info))

    def do_identify(self):
        """Information about the .vob file"""
        print "**** Information on:", self.f_input
        ps = Popen([self.mplayerid, "-identify", "-frames", "0",
                    "-msglevel", "identify=6", "-vo", "null", "-ao", "null",
                    self.f_input],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dat = ps.stdout.read()
        dat = dat.split('\n')
        dat = [ l for l in dat if "AUDIO_ID" in l
                               or "SUBTITLE_ID" in l
                               or "VIDEO_ID" in l ]
        print "\n".join(dat)
        print
        return dat
    def do_detecttc(self):
        """Run through the video as fast as possible, to find framerate changes
        """
        cmd = [self.mplayerid, self.f_input,
               '-nosound', '-vo', 'null', '-benchmark']
        call(cmd)

    def do_subs(self):
        print "**** Subtitles", self.subtitles
        # subtitles:
        for sid, lang in sorted(self.subtitles.items()):
            # We have to delete these files first.  It appends to
            # them, not overwrites them like other outputters do.
            for fname in (self.f_sub(sid), self.f_subsub(sid),
                          self.f_subidx(sid)):
                if os.access(fname, os.F_OK):
                    os.unlink(fname)
            # Do the dumping.
            cmd = [ self.mencoder, "-oac", "copy", "-ovc", "copy",
                    "-ofps", str(self.fps), "-o", "/dev/null",
                    "-sid", str(sid), "-vobsubout", self.f_sub(sid),
                    self.f_input, ]
            print cmd
            call(cmd)


    def do_audio(self):
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
              ] + self.mencoderopts

        oggquality = self.oggquality
        if self.oggquality_aid and aid in self.oggquality_aid:
            oggquality = self.oggquality_aid[aid]
        # Run in foreground
        oggenc = ["oggenc",
              "-q"+str(oggquality),
              "--title", self.audio[aid],  # Could be made "English"
              "--quiet",
              "--raw-rate", self.audio_rawrate,
              "-o"+self.f_audio_final(aid),
              self.f_audio_fifo(aid),
              ]
        print mencoder
        print oggenc
        Popen(mencoder)
        time.sleep(1)
        ret = call(oggenc)
        assert not ret, "Audio encoding failed: %s:%s"%(aid,self.audio[aid])
        os.unlink(self.f_audio_fifo(aid))



    def do_video(self):
        print "****Video"
        if not os.access(self.f_video_fifo, os.F_OK):
            os.mkfifo(self.f_video_fifo)

        mencoder = [self.mencoder,
                    "-quiet", "-sid", "2999", # dummy sid to disable them.
                    "-oac", "copy", "-ovc", "raw", "-of", "rawvideo",
                    "-ofps", self.fps,
                    "-o", self.f_video_fifo,
                    #-vf crop=720:464:0:6,scale=704:384,dsize=-1,format=I420
                    self.f_input]
        if self.vf:
            mencoder[1:1] = ["-vf", self.vf+",dsize=-1,format=I420"]
        else:
            mencoder[1:1] = ["-vf", "dsize=-1,format=I420"]
        mencoder[1:1] = self.mencoderopts

        #if var.has_key("mplayeropts"):
        #    mencoder[1:1] = var["mplayeropts"]
        # check aspect for x264
        aspect = self.aspect
        aspect = aspect.replace("/", ":")
        if aspect.find(':') == -1:
            aspect = "1:"+aspect   # it should be w:h (?)
        x264 = [self.x264,
                #"--progress",
                "--sar", aspect,
                "--stats", self.f_x264log,
                "--fps", self.fps,
                "--threads", str(self.threads),
                #"--verbose",
                self.f_video_fifo, self.xysize ]

        x264[1:1] = self.x264opts

        if self.vbitrate:
            x264[1:1] = ["--bitrate", str(self.vbitrate)]
        elif self.qp:
            x264[1:1] = ["--qp", str(self.qp)]
        elif self.crf:
            x264[1:1] = ["--crf", str(self.crf)]
        elif self.x264preset:
            x264[1:1] = ["--preset", str(self.x264preset)]
        else:
            print "either key of 'vbitrate', 'qp', 'crf', or 'x264preset' must be specified."
            sys.exit()

        # "crf" is a one-pass encoding.
        if self.crf or self.x264preset:
            x264[1:1] = ["-o", self.f_video_final]
            x264[1:1] = self.x264opts_pass2

            print "****Beginning only pass (with crf)"
            print mencoder
            print x264
            Popen(mencoder)
            time.sleep(1)
            call(x264)

        else:
            x264_pass1 = x264[:]
            x264_pass2 = x264[:]

            x264_pass1[1:1] = ["--pass", "1"]
            x264_pass1[1:1] = ["-o", "/dev/null"]
            x264_pass1[1:1] = self.x264opts_pass1

            x264_pass2[1:1] = ["--pass", "2"]
            x264_pass2[1:1] = ["-o", self.f_video_final]
            x264_pass2[1:1] = self.x264opts_pass2

            print "****Beginning pass 1"
            print mencoder
            print x264_pass1
            Popen(mencoder)
            time.sleep(1)
            call(x264_pass1)

            print "****Beginning pass 2"
            print mencoder
            print x264_pass2
            Popen(mencoder)
            time.sleep(1)
            call(x264_pass2)

        print "****Done with video encoding"
        os.unlink(self.f_video_fifo)


    def do_merge(self):
        print "****Merging..."

        # Metadata part
        mkvmerge = ["mkvmerge",
                    "--default-duration", self.fps.replace("/",':')+'fps',
                    "--chapters", self.f_chapters,
                    "--title",  self.title]
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
        call(mkvmerge)


class Episode(Film):
    """Part of a tv show.

    Defines 'seriestitle', 'season', and 'episode' as extra attributes."""
    #seriestitle = ""
    #season = 1

    def __init__(self, title,
                 seriestitle=None,
                 season=None, episode=None, **kwargs):
        super(Episode, self).__init__(title=title, **kwargs)
        if season:       self.season      = season
        if seriestitle:  self.seriestitle = seriestitle
        if episode:      self.episode     = episode

    @property
    def SxEid(self):
        try:
            return "%(season)dx%(episode)02d"%self
        except TypeError:
            return "%(season)sx%(episode)s"%self
    @property
    def f_basename(self):
        return "%(SxEid)s - %(title)s%(groupid)s"%self
    @property
    def mkv_title(self):
        if self.seriestitle:
            return "%s %(SxEid)s - %s"%(self.seriestitle, self.SxEid, self.title)


