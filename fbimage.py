#!/usr/bin/python2
from __future__ import print_function
import sys
from pgmagick import *
from fb import framebuffer

def fbimage(image, color="black", margin=0, stretch=False, device="/dev/fb0", debug=False):

    input = sys.stdin if image == '-' else open(image)

    # open framebuffer so we can get its geometry
    fb=framebuffer(device)
    if debug: print("frame buffer height=%d width=%d" % (fb.height, fb.width))

    # create background layer
    base=Image(Geometry(fb.width, fb.height), Color(color))
    base.fillColor(Color(color))
    base.strokeWidth(0)

    im=Image(Blob(input.read()))
    if debug: print("original image height=%d width=%d" % (im.rows(), im.columns()))

    g=Geometry(fb.width-(margin*2), fb.height-(margin*2))
    if stretch: g.aspect(True)
    im.scale(g)
    if debug: print("scaled image height=%d width=%d" % (im.rows(), im.columns()))

    base.composite(im, GravityType.CenterGravity, CompositeOperator.OverCompositeOp)

    blob=Blob()
    base.write(blob,"RGB",8)
    fb.pack(blob.data)
