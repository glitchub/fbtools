# Graphic image using pgmagick, works with python 2 or 3
# See https://www.imagemagick.org/Magick++/Image++.html for C++ API which is
# directly exposed by the python module.

from __future__ import print_function, division
import os, sys
from pgmagick import *

# directory containing this module also contains needed fonts
__here__ = os.path.dirname(__file__) or '.'

# default font is monospaced
__font__ = __here__ + "/WenQuanYiMicroHeiMono.ttf"

# dict of gravities
gravities={ "nw": GravityType.NorthWestGravity,
            "n":  GravityType.NorthGravity,
            "ne": GravityType.NorthEastGravity,
            "w":  GravityType.WestGravity,
            "c":  GravityType.CenterGravity,
            "e":  GravityType.EastGravity,
            "sw": GravityType.SouthWestGravity,
            "s":  GravityType.SouthGravity,
            "se": GravityType.SouthEastGravity }

# python version-agnostic convert object to str or bytes
def _to_str(s):
    try:
        return s.decode('utf-8')
    except:
        return str(s)

def _to_bytes(s):
    try:
        return bytes(s, 'utf-8')
    except:
        return bytes(s)

class image():

    def __init__(
            self,
            width=None, height=None,    # image size
            bg="black", fg="white",     # default colors
            rgb=None                    # init with rgb data (must be the correct size)
        ):

        self.width = width
        self.height = height
        self.fg = fg
        self.bg = bg

        if rgb:
            self.image = Image(Blob(rgb), Geometry(width, height), 8, "RGB")
        else:
            self.image = Image(Geometry(width, height), Color(bg))

    # create transparent layer for subsequent overlay
    def layer(self, width=None, height=None):
        return Image(Geometry(width or self.width, height or self.height), Color("transparent"))

    # overlay image with l at specified offset or with specified gravity
    def overlay(self, l, pos=(0,0)):
        if type(pos) in [list, tuple]:
            pos=Geometry(0,0,pos[0],pos[1]) # see http://www.graphicsmagick.org/Magick++/Geometry.html
        else:
            pos=gravities[pos]
        self.image.composite(l, pos, CompositeOperator.OverCompositeOp)

    # Draw a border in fg color on edge of the image
    def border(self, width):
        self.image.strokeWidth(width)
        self.image.strokeColor(self.fg)
        self.image.fillColor("transparent")
        self.image.draw(DrawableRectangle(0, 0, self.width-1, self.height-1))

    # Given filename or list of textlines, write text to image in fg color
    def text(
            self,
            text,                    # text to display, can contain tabs and linefeeds.
            left=0, top=0,           # offset on image
            width=None, height=None, # size of text frame
            box=None,                # if defined, specified ulhc and lrhc coords, overrides top, left, width, height
            gravity = 'nw',          # one of nw, n, ne, w, c, e, sw, s, s.
            wrap = False,            # wrap lines at right margin
            clip = None,             # clip text at margins
            point = 20,              # pointsize
            font = __font__          # font
        ):

        # convert text to list of lines
        text=[s.expandtabs() for s in text.splitlines()]

        if clip is None: clip = wrap

        if box:
            # box is (left, top, right, bottom)
            left = box[0]
            top = box[1]
            width = (box[2]-box[0])+1
            height = (box[3]-box[1])+1
        else:
            if height is None: height is self.height
            if width is None: width is self.width

        # keep it real
        left = int(left)
        top = int(top)
        height = int(height)
        width = int(width)

        # write text to a layer
        l = self.layer(width, height)
        l.font(font)
        l.fontPointsize(point)
        tm = TypeMetric()
        l.fontTypeMetrics("M",tm)

        # the y offset is based on font and gravity
        if gravity in ("nw","n","ne"): yoffset = tm.ascent()
        elif gravity in ("sw","s","se"): yoffset = -tm.descent()
        else: yoffset=0

        maxcols = int(width // tm.textWidth())
        maxlines = int(height // (tm.textHeight()+1))

        if wrap:
            # wrap text to fit... this fails for characters wider than 'M'
            def wrapt(t):
                t = t.rstrip(' ')
                while len(t) > maxcols:
                    i = t[:maxcols].rfind(' ')
                    if (i < 0):
                        yield t[:maxcols]
                        t = t[maxcols:]
                    else:
                        yield t[:i]
                        t = t[i+1:]
                    t = t.rstrip(' ')
                yield t
            text = [w for t in text for w in wrapt(t)]

        if clip:
            text = text[:maxlines]
            text = [s[:maxcols] for s in text] # does nothing if wrapped

        if text:
            # If text remains, write it to the layer with gravity
            l.strokeWidth(0)
            l.fillColor(self.fg)
            # XXX can this be done with Image.annotate()?
            d = DrawableList()
            d.append(DrawableGravity(gravities[gravity]))
            d.append(DrawableText(0, yoffset, '\n'.join(text)))
            l.draw(d)

            self.overlay(l, (left, top))

    # Load an image file and scale/stretch.
    def read(
            self,
            filename,       # a filename, '-' for stdin, prefix with FMT: to force format
            margin=0,       # pixels to leave around edge of image
            stretch=False   # stretch image to fit image
        ):

        if filename == '-':
            try: fh = sys.stdin.buffer # python 3
            except: fh = sys.stdin     # python 2
        else:
            fh = open(filename, mode='rb')

        l=Image(Blob(fh.read()))
        g=Geometry(self.width-(margin*2), self.height-(margin*2))
        if stretch: g.aspect(True)
        l.scale(g)
        self.overlay(l,'c')

    # Write the image to a file or stdout. Format is determined from file
    # extent or leading "FMT:" tag (e.g "PNG:data").
    def write(self, filename):
        self.image.write(filename)

    # Return image raw RGB data
    def rgb(self):
        blob=Blob()
        self.image.write(blob, "RGB", 8)
        return blob.data
