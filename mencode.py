#!/usr/bin/env python
import os
import sys

class Var(dict):
    def __init__(self, d):
        for k,v in d.interitems():
            self.k = v
    def __getattr__(self, k):
        return self[k].getattr(self, k)
var = {}
var["origfname"] = "rambo2.mpg"
var["syncMplayerOpts"] = ["-vf", "harddup", "-ofps", "24000/1001"]
var["title"] = "Rambo: First Blood Part 2"
var["fname"] = var["origfname"] + ".norm.avi"
var["vf"] = "crop=720:368:0:54"
var["aspect"] = "2.35"
var["vbitrate"] = 975

audio = [{"aid": 128,
          "oggquality": 3,
          "tracktitle": "English",
          "language": "en",
          },
         {"aid": 130,
          "oggquality": 0,
          "tracktitle": "French",
          "language": "fr",
          },
         {"aid": 131,
          "oggquality": -1,
          "tracktitle": "Director's Commentary",
          "language": "xx",
          },
         ]
var["audio"] = audio

doaudio=True
dovideo=True

#x264 = "x264"
x264path = "/home/richard/sys/x264/x264/x264"

# audio tracks:
# 128 - 
# 137 -
# 130 - 
# 131 -


#
# Function Definitions
#
def normcopy(var):
    mencoder = ["mencoder",
                "-oac", "copy", "-ovc", "copy",
                "-o", var["fname"], var["origfname"]]
    mencoder[1:1] = var["syncMplayerOpts"]
    if var.has_key("aid"):
        mencoder[1:1] = ["-aid", str(var["aid"])]
    print mencoder
    os.spawnvp(os.P_WAIT, "mencoder", ("mencoder"))
    x = os.spawnvp(os.P_WAIT, "mencoder", mencoder)
    if x:
        print "error", x ; sys.exit()    

def audioencode(var):
    # This function uses variables from the outside scope to command it.
    normcopy(var)
    oggenc = ["oggenc",
              "-q"+str(var["oggquality"]),
              "-t", var["tracktitle"],
              "--quiet", "-o"+var["audiofname"],
              "tmp.audio.pipe.wav",
              ]
    mplayer = ["mplayer", var["fname"],
               "-hardframedrop", "-vc", "null", "-vo", "null",
               "-ao", "pcm:file=tmp.audio.pipe.wav:fast"]
    os.spawnvp(os.P_NOWAIT, "oggenc", oggenc)
    os.spawnvp(os.P_WAIT, "mplayer", mplayer)

# 
# audio part
# 
def doaudio(var):
    audio = var["audio"]
    os.system("mkfifo tmp.audio.pipe.wav")
    for i, a in enumerate(audio):
        print "****Audio track", i
        a["newindex"] = i
        a["audiofname"] = "audio"+str(i)+".ogg"
        var2 = var.copy()
        var2.update(a)
        normcopy(var2)
        audioencode(var2)
    os.system("tmp.audio.pipe.wav")

# 
# Video Part
#    
def dovideo(var):
    # This copy below isn't needed if the audio copies from above are left over
    print "****Beginning video stuff"
    if not doaudio: 
        print "****Making a working copy of video"
        normcopy(var)
    
    os.system("mkfifo tmp.video.pipe.y4m")
    print "****Beginning pass 1"
    mplayer = ["mplayer",
               "-vo", "yuv4mpeg:file=tmp.video.pipe.y4m",
               "-ac", "dummy", "-ao", "null",
               var["fname"]]
    if var.has_key("vf"):
        mplayer[1:1] = ["-vf", var["vf"]]
    if var.has_key("mplayeropts"):
        mplayer[1:1] = var["mplayeropts"]
    x264 = [x264path,
            "--progress",
            "--threads", "2",
            "--pass", "1",
            "--bitrate", var["vbitrate"],
            "--bframes", "2",
            "--subme", "2",
            "--stats", "x264_2pass.log",
            "-o", "/dev/null",
            "tmp.video.pipe.y4m"]
    os.spawnvp(os.P_NOWAIT, "mplayer", mplayer)
    os.spawnvp(os.P_WAIT, x264path, x264)

    print "****Beginning pass 2"
    mplayer = ["mplayer",
               "-vo", "yuv4mpeg:file=tmp.video.pipe.y4m",
               "-ac", "dummy", "-ao", "null",
               var["fname"]]
    if var.has_key("vf"):
        mplayer[1:1] = ["-vf", var["vf"]]
    if var.has_key("mplayeropts"):
        mplayer[1:1] = var["mplayeropts"]
    x264 = [x264path,
            "--progress",
            "--threads", "2",
            "--pass", "2",
            "--bitrate", var["vbitrate"],
            "--bframes", "2",
            "--subme", "6",
            "--trellis", "1",
            "--ref", "4",
            "--8x8dct",
            "--stats" "x264_2pass.log",
            "-o", "video.x264.mkv", "tmp.video.pipe.y4m"]
    os.spawnvp(os.P_NOWAIT, "mplayer", mplayer)
    os.spawnvp(os.P_WAIT, x264path, x264)

    print "****Done with video encoding"
    os.system("rm tmp.video.pipe.y4m")
    
    
def merge(var):
    print "****Merging..."
    mkvmerge = ["mkvmerge",
                "--title",  var["title"],
                "--noaudio", "video.x264.mkv"]
    for i, a in enumerate(audio):
        y = ["--no-video", a["audiofname"] ]
        if a.has_key("language"):
            y[0:0] = ["--language", "0:"+a["language"]]
        mkvmerge.extend(9)
    mkvmerge.extend(["-o", var["origfname"]+".x264."+var["vbitrate"]+".mkv"])

def doall(var):
    doaudio(var)
    dovideo(var)
    doall(var)

if __name__ == "__main__":
    doall(var)
