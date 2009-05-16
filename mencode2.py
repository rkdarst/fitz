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
var["origfname"] = "rambo2.mpg"
#var["syncMplayerOpts"] = ["-vf", "harddup", "-ofps", "24000/1001"]
var["title"] = "Rambo: First Blood Part 2"
#var["fname"] = var["origfname"] + ".norm.avi"
var["fname"] = var["origfname"]
var["vf"] = "crop=720:368:0:54"
var["aspect"] = "2.35"   # like 4/3, 16/9, 2.35
var["vbitrate"] = 975
# var["qp"] = 20
var["xysize"] = "720x368" # final size
var["fps"] = "24000/1001"
var["audioRawRate"] = "48000"
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

def audioencode(var):
    # This function uses variables from the outside scope to command it.
    oggenc = ["oggenc",
              "-q"+str(var["oggquality"]),
              "-t", var["tracktitle"],
              "--quiet",
              "--raw-rate", var["audioRawRate"],
              "-o"+var["audiofname"],
              "tmp.audio.pipe.wav",
              ]
    mencoder = ["mencoder",
                "-ovc", "copy", "-vc", "dummy",
                "-aid", str(var["aid"]),
                "-of", "rawaudio", "-oac", "pcm",
                "-af", "format=s16le",
                "-o", "tmp.audio.pipe.wav",
                var["fname"],
                ]
    os.spawnvp(os.P_NOWAIT, "oggenc", oggenc)
    os.spawnvp(os.P_WAIT, "mencoder", mencoder)

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
        audioencode(var2)
    os.system("rm tmp.audio.pipe.wav")

# 
# Video Part
#    
def dovideo(var):
    # This copy below isn't needed if the audio copies from above are left over
    print "****Beginning video stuff"
    os.system("mkfifo tmp.video.pipe.raw")
    
    mencoder = ["mencoder",
                "-oac", "copy", "-ovc", "raw", "-of", "rawvideo",
                "-o", "tmp.video.pipe.raw",
                "-ofps", var["fps"],
                #-vf crop=720:464:0:6,scale=704:384,dsize=-1,format=I420
                var["fname"]]
    if var.has_key("vf"):
        mencoder[1:1] = ["-vf", var["vf"]+",dsize=-1,format=I420"]
    else:
        mencoder[1:1] = ["-vf", "dsize=-1,format=I420"]
        
    #if var.has_key("mplayeropts"):
    #    mencoder[1:1] = var["mplayeropts"]
    x264 = [x264path,
            "--progress",
            "--stats", "x264_2pass.log",
            "tmp.video.pipe.raw", var["xysize"], "--fps", var["fps"]]

    x264[1:1] = var["x264opts_both"]

    if var.has_key("vbitrate"):
        x264[1:1] = ["--bitrate", str(var["vbitrate"])]
    elif var.has_key("qp"):
        x264[1:1] = ["--qp", str(var["qp"])]
    elif var.has_key("crf"):
        x264[1:1] = ["--crf", str(var["crf"])]
    else:
        print "either key of 'vbitrate', 'qp', or 'crf' must be specified."
        sys.exit()

    if var.has_key("crf"):
        x264_pass2 = x264[:]
        #x264_pass2[1:1] = ["--pass", "2"]
        x264_pass2[1:1] = ["-o", "video.x264.mkv"]
        x264_pass2[1:1] = var["x264opts_pass2"]

        print "****Beginning pass 2 (with crf)"
        os.spawnvp(os.P_NOWAIT, "mencoder", mencoder)
        os.spawnvp(os.P_WAIT, x264path, x264_pass2)

    else:
        x264_pass1 = x264[:]
        x264_pass2 = x264[:]
    
        x264_pass1[1:1] = ["--pass", "1"]
        x264_pass1[1:1] = ["-o", "/dev/null"]
        x264_pass2[1:1] = var["x264opts_pass1"]
    
        x264_pass2[1:1] = ["--pass", "2"]
        x264_pass2[1:1] = ["-o", "video.x264.mkv"]
        x264_pass2[1:1] = var["x264opts_pass2"]
    
        print "****Beginning pass 1"
        os.spawnvp(os.P_NOWAIT, "mencoder", mencoder)
        os.spawnvp(os.P_WAIT, x264path, x264_pass1)
    
        print "****Beginning pass 2"
        os.spawnvp(os.P_NOWAIT, "mencoder", mencoder)
        os.spawnvp(os.P_WAIT, x264path, x264_pass2)

    print "****Done with video encoding"
    os.system("rm tmp.video.pipe.raw")
    
    
def merge(var):
    print "****Merging..."
    audio = var["audio"]
    mkvmerge = ["mkvmerge",
                "--title",  var["title"],
                "--noaudio", ]
    if var.has_key("aspect"):
        mkvmerge.extend(["--aspect-ratio", "1:"+var["aspect"]])
    mkvmerge.append("video.x264.mkv")
    
    for i, a in enumerate(audio):
        a["audiofname"] = "audio"+str(i)+".ogg"
        y = ["--novideo", a["audiofname"] ]
        if a.has_key("language"):
            y[0:0] = ["--language", "0:"+a["language"]]
        mkvmerge.extend(y)
    # what output filename to use:
    if var.has_key("vbitrate"):
        brname = str(var["vbitrate"])
    elif var.has_key("qp"):
        brname = "q"+str(var["qp"])
    elif var.has_key("crf"):
        brname = "c"+str(var["crf"])
    else:
        brname = "x"

    mkvmerge.extend(["-o", var["origfname"]+".x264."+brname+".mkv"])
    os.spawnvp(os.P_WAIT, "mkvmerge", mkvmerge)

def doall(var):
    doaudio(var)
    dovideo(var)
    merge(var)
    
if __name__ == "__main__":
    doall(var)
