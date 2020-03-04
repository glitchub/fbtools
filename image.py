# Graphic image using pgmagick, works with python 2 or 3

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

class draw():
    def __init__(self):
        self.dl = DrawableList()

    def draw(self, image):
        image.draw(self.dl)
        self.dl=DrawableList()

    def stroke(self, width):
        self.dl.append(DrawableStrokeWidth(width))

    def color(self, color):
        self.dl.append(DrawableStrokeColor(Color(color)))

    def fill(self, color):
        self.dl.append(DrawableFillColor(Color(color)))

    def gravity(self, gravity):
        self.dl.append(DrawableGravity(gravities[gravity]))

    def rectangle(self, left, top, width, height):
        self.dl.append(DrawableRectangle(left, top, left+width-1, top+height-1))

    def text(self, left, top, text):
        self.dl.append(DrawableText(left, top, _to_bytes(text)))

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

    # overlay image l, at specified offset or with specified gravity
    def overlay(self, l, pos=(0,0)):
        if type(pos) in [list, tuple]:
            pos=Geometry(0,0,pos[0],pos[1])
        else:
            pos=gravities[pos]
        self.image.composite(l, pos, CompositeOperator.OverCompositeOp)

    # Draw a border in fg color on edge of the image
    def border(self, width):
        l = self.layer()
        l.stroke_width(width)
        l.stroke_color(self.fg)
        l.fill_color("transparent")
        l.draw(DrawableRectangle(0, 0, self.width, self.height))
        self.overlay(l)

    # Given filename or list of textlines, write text to image in fg color
    def text(
            self,
            input,                   # a filename, or a list of text lines
            height=None, width=None, # size of text frame
            left=0, top=0,           # offset on image
            gravity = 'nw',          # one of nw, n, ne, w, c, e, sw, s, s.
            wrap = False,            # wrap lines at right margin
            clip = None,             # clip text at margins
            point = 20,              # pointsize
            font = __font__          # font
        ):
        if type(input) is list:
            # clean up the list
            text = [_to_str(s).expandtabs() for s in input]
        else:
            if input == '-':
                try: fh = sys.stdin.buffer # python 3
                except: fh = sys.stdin     # python 2
            else:
                fh = open(input, mode='rb')
            text = [ s.expandtabs() for s in _to_str(fh.read()).splitlines() ]
            fh.close()

        if clip is None: clip = wrap
        if height is None: height is self.height
        if width is None: width is self.width

        l=self.layer()
        l.font(font)
        l.fontPointsize(point)
        tm = TypeMetric()
        l.fontTypeMetrics("M",tm)

        #  y offset is based on gravity
        if gravity in ("nw","n","ne"):
            yoffset = tm.ascent()
        elif gravity in ("sw","s","se"):
            yoffset = -tm.descent()
        else:
            yoffset=0

        maxcols = int(width // tm.textWidth())
        maxlines = int(height // (tm.textHeight()+1))

        if wrap:
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

        l.stroke_width(0)
        l.fill_color(self.fg)

        d = draw()
        d.gravity(gravity)
        d.text(0, yoffset, '\n'.join(text))
        d.draw(l)

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
