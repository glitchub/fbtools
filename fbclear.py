#!/usr/bin/python2
from pgmagick import *
from fb import framebuffer

def fbclear(color="black", device="/dev/fb0"):
    fb=framebuffer(device)
    im=Image(Geometry(fb.width, fb.height), Color(color))
    blob=Blob()
    im.write(blob,"RGB",8)
    fb.pack(blob.data)
