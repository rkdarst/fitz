#!/usr/bin/env python
import os
import sys

# Usage:
# - Copy all the "var = " stuff into yourscript.py
# - Adjust "var = " stuff to fit your needs
# - put "import mencode2" at the top of it
# - run mencode2.doall(var) last thing
# - run your python script: "python yourscript.py"

var = {}
var["input"] = "utah2.mpg"
var["output"] = var["input"]
var["mplayeropts"] = ["-vf", "harddup"]
var["title"] = "Utahraptor Revenge 2"
#var["fname"] = var["origfname"] + ".norm.avi"
#var["vf"] = "crop=720:368:0:54"
var["aspect"] = "2.35"   # like 4/3, 16/9, 2.35
var["xysize"] = "720x368" # final size
#var["fps"] = "24000/1001"


# You need to pick one of the following modes of encoding.  I
# recommend either "crf" for constant-quality if you don't care about
# total size, or if not "vbitrate" for choosing a overall bitrate with
# two-pass encoding.
#--------------------------
# Constant quality mode.  If "crf" is present, it is a one-pass
# encoding, which only uses x264opts_both and x242opts_pass2.  See
# `x264 --help`.
var["crf"] = 23
# In this mode, also look at these types of options:
#var["x264opts_both"] = ['--preset', 'veryslow',
#                        '--tune', 'film',
#                        ]
#--------------------------
# Set the overall bitrate.  This will do two-pass, using "--bitrate
# NNN" and the x264 two-pass options
var["vbitrate"] = 975
#--------------------------
# This is just like above, but specifies a constast quantizer.  Still
# does two pass.  Constant quality (above) is better.
var["qp"] = 30
#--------------------------

var["x264opts_both"] = ["--threads", "2",
#                        "--bitrate", str(var["vbitrate"]),
                        "--ref", "4",
                        "--bframes", "3",
                        ]
var["x264opts_pass1"] = ["--subme", "2",
                         ]
var["x264opts_pass2"] = ["--subme", "6",
                         "--me", "umh",
                         "--weightb",
                         "--bime",
                         "--b-rdo",
                         "--mixed-refs",
                         #"--trellis", "1",
                         "--8x8dct",
                         ]

var["audioRawRate"] = "48000"
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


# Override  these globals
x264path = "/home/richard/sys/x264/x264"
mencoderpath = "/home/richard/sys/MPlayer-1.0rc1/mencoder"

#
# Useful mpencoder keys:
#
# v - Toggle subtitle visibility.
# j - Cycle through the available subtitles.



#
# Function Definitions
#

def maketmpnames(var):
    basename = var["input"].replace("://","") # for dvd:// -type names
    audio = var["audio"]
    for i, a in enumerate(audio):
        a["newindex"] = i
        a["audiofname"] = "tmp."+basename+".audio."+str(a['aid'])+".ogg"
        audiopipe = 'tmp.'+basename+'.audio.'+str(a['aid'])+'.pipe.wav'
        a['audiopipe'] = audiopipe

    videopipe = "tmp."+basename+".video.pipe.raw"
    var["videopipe"] = videopipe
    videotmp = "tmp."+basename+".video.mkv"
    var["videotmp"] = videotmp
    var["x264log"] = basename+".x264_2pass.log"

def audioencode(var):
    # This function uses variables from the outside scope to command it.
    oggenc = ["oggenc",
              "-q"+str(var["oggquality"]),
              "-t", var["tracktitle"],
              "--quiet",
              "--raw-rate", var["audioRawRate"],
              "-o"+var["audiofname"],
              var['audiopipe'],
              ]
    mencoder = [mencoderpath,
                "-ovc", "copy", "-vc", "dummy",
                "-aid", str(var["aid"]),
                "-of", "rawaudio", "-oac", "pcm",
                "-af", "format=s16le",
                "-o", var['audiopipe'],
                var["input"],
                ]
    if "mencoderopts" in var:
        mencoder[1:1] = var["mencoderopts"]
    #os.spawnvp(os.P_NOWAIT, "oggenc", oggenc)
    #os.spawnvp(os.P_WAIT, "mencoder", mencoder)
    os.spawnvp(os.P_NOWAIT, mencoderpath, mencoder)
    os.spawnvp(os.P_WAIT, "oggenc", oggenc)

# 
# audio part
# 
def doaudio(var):
    audio = var["audio"]
    for i, a in enumerate(audio):
        print "****Audio track", i
        #a["newindex"] = i
        #a["audiofname"] = "tmp."+var["input"]+".audio."+str(a['aid'])+".ogg"
        #audiopipe = 'tmp.'+var['input']+'.audio.'+str(a['aid'])+'.pipe.wav'
        #a['audiopipe'] = audiopipe
        os.system("mkfifo "+a["audiopipe"])
        var2 = var.copy()
        var2.update(a)
        audioencode(var2)
        os.system("rm "+a["audiopipe"])

# 
# Video Part
#    
def dovideo(var):
    # This copy below isn't needed if the audio copies from above are left over
    print "****Beginning video stuff"
    #videopipe = "tmp."+var["input"]+".video.pipe.raw"
    #videotmp = "tmp."+var["input"]+".video.mkv"
    #var["videotmp"] = videotmp
    videopipe = var["videopipe"]
    videotmp = var["videotmp"]
    os.system("mkfifo "+videopipe)
    
    mencoder = [mencoderpath,
                #"-quiet",
                "-oac", "copy", "-ovc", "raw", "-of", "rawvideo",
                "-ofps", var["fps"],
                "-o", videopipe,
                #-vf crop=720:464:0:6,scale=704:384,dsize=-1,format=I420
                var["input"]]
    if "vf" in var:
        mencoder[1:1] = ["-vf", var["vf"]+",dsize=-1,format=I420"]
    else:
        mencoder[1:1] = ["-vf", "dsize=-1,format=I420"]
    if "mencoderopts" in var:
        mencoder[1:1] = var["mencoderopts"]
        
    #if var.has_key("mplayeropts"):
    #    mencoder[1:1] = var["mplayeropts"]
    # check aspect for x264
    aspect = var["aspect"]
    aspect.replace("/", ":")
    if aspect.find(':') == -1:
        aspect = "1:"+aspect   # does this make sense?  it should be w:h
    x264 = [x264path,
            #"--progress",
            "--stats", "tmp."+var["x264log"],
            videopipe, var["xysize"], "--fps", var["fps"],
            "--sar", aspect,
            "--verbose"]

    if "x264opts_both" in var:
        x264[1:1] = var["x264opts_both"]

    if "vbitrate" in var:
        x264[1:1] = ["--bitrate", str(var["vbitrate"])]
    elif "qp" in var:
        x264[1:1] = ["--qp", str(var["qp"])]
    elif "crf" in var:
        x264[1:1] = ["--crf", str(var["crf"])]
    else:
        print "either key of 'vbitrate', 'qp', or 'crf' must be specified."
        sys.exit()

    # "crf" is a one-pass encoding.
    if var.has_key("crf"):
        x264_pass2 = x264[:]
        #x264_pass2[1:1] = ["--pass", "2"]
        x264_pass2[1:1] = ["-o", videotmp]
        if "x264opts_pass2" in var:
            x264_pass2[1:1] = var["x264opts_pass2"]

        print "****Beginning pass 2 (with crf)"
        os.spawnvp(os.P_NOWAIT, mencoderpath, mencoder)
        os.spawnvp(os.P_WAIT, x264path, x264_pass2)

    else:
        x264_pass1 = x264[:]
        x264_pass2 = x264[:]
    
        x264_pass1[1:1] = ["--pass", "1"]
        x264_pass1[1:1] = ["-o", "/dev/null"]
        if "x264opts_pass1" in var:
            x264_pass2[1:1] = var["x264opts_pass1"]
    
        x264_pass2[1:1] = ["--pass", "2"]
        x264_pass2[1:1] = ["-o", videotmp]
        if "x264opts_pass2" in var:
            x264_pass2[1:1] = var["x264opts_pass2"]
    
        print "****Beginning pass 1"
        os.spawnvp(os.P_NOWAIT, mencoderpath, mencoder)
        os.spawnvp(os.P_WAIT, x264path, x264_pass1)
    
        print "****Beginning pass 2"
        os.spawnvp(os.P_NOWAIT, mencoderpath, mencoder)
        os.spawnvp(os.P_WAIT, x264path, x264_pass2)

    print "****Done with video encoding"
    os.system("rm "+videopipe)
    
    
def merge(var):
    print "****Merging..."
    audio = var["audio"]
    mkvmerge = ["mkvmerge",
                "--title",  var["title"],
                "--noaudio", ]
    if "aspect" in var:
        mkvmerge.extend(["--aspect-ratio", "1:"+var["aspect"]])
    mkvmerge.append(var["videotmp"])

    for i, a in enumerate(audio):
        #a["audiofname"] = a["audiofname"]
        y = ["--novideo", a["audiofname"] ]
        if a.has_key("language"):
            y[0:0] = ["--language", "0:"+a["language"]]
        mkvmerge.extend(y)
    # what output filename to use:
    if "vbitrate" in var:
        brname = str(var["vbitrate"])
    elif "qp" in var:
        brname = "q"+str(var["qp"])
    elif "crf" in var:
        brname = "c"+str(var["crf"])
    else:
        brname = "x"

    mkvmerge.extend(["-o", var["output"]+".x264."+brname+".mkv"])
    os.spawnvp(os.P_WAIT, "mkvmerge", mkvmerge)

def doall(var):
    maketmpnames(var)
    doaudio(var)
    dovideo(var)
    merge(var)
    
if __name__ == "__main__":
    doall(var)


# Here is one example of a sample script.  Basically use this
# interface to design a script to do what you need to do:
'''
var = { }
var["input"] = "d1-1.dump"
var["output"] = "btvs401"
var["title"] = "BTvS - 4.01"
var["aspect"] = "4/3"
var["fps"] = "24000/1001"
#var["xysize"] = "720x480"
var["xysize"] = "540x360"
var["vf"] = "yadif,scale=540:360"
#var["mencoderopts"] = ["-endpos", "4:00"]
var["audioRawRate"] = "48000"

var["crf"] = 23
var["x264opts_both"] = ['--preset', 'veryslow',
                        '--tune', 'film',
                        ]

audio = [{"aid": 128,
          "oggquality": 3,
          "tracktitle": "English",
          "language": "en",
          },
          #{"aid": 129,
          # "oggquality": 1,
          # "tracktitle": "French",
          # "language": "fr",
          # },
          #{"aid": 130,
          # "oggquality": 1,
          # "tracktitle": "Spanish",
          # "language": "es",
          # },
          ]
var['audio'] = audio


# Individual pieces (for testing):
#mencode2.maketmpnames(var)
#mencode2.doaudio(var)
#mencode2.dovideo(var)
#mencode2.merge(var)

# All at once (calls the function above in sequence):
mencode2.doall(var)
'''
