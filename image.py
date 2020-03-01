# Graphic image using pgmagick, works with python 2 or 3

from __future__ import print_function, division
import os, sys
from pgmagick import *

# directory containing this module also contains needed fonts
__here__ = os.path.dirname(__file__) or '.'

# default font is monospaced
__font__ = __here__ + "/WenQuanYiMicroHeiMono.ttf"

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
    # create an image of specified size and color
    width=None
    height=None
    fg=None
    bg=None
    image=None

    gravities={ "nw": GravityType.NorthWestGravity,
                "n":  GravityType.NorthGravity,
                "ne": GravityType.NorthEastGravity,
                "w":  GravityType.WestGravity,
                "c":  GravityType.CenterGravity,
                "e":  GravityType.EastGravity,
                "sw": GravityType.SouthWestGravity,
                "s":  GravityType.SouthGravity,
                "se": GravityType.SouthEastGravity }

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

        self.image.fillColor(Color(fg))
        self.image.strokeWidth(0)

    # Draw a border in fg color on edge of the image
    def border(
            self,
            pixels # border width in pixels
        ):
        if pixels == 1:
            self.image.draw(DrawableLine(0, 0, self.width-1, 0)) # across the top
            self.image.draw(DrawableLine(0, 0, 0, self.height-1)) # down the left
            self.image.draw(DrawableLine(self.width-1, 0, self.width-1, self.height-1)) # down the right
            self.image.draw(DrawableLine(0, self.height-1, self.width-1, self.height-1)) # across the bottom
        elif pixels > 1:
            self.image.draw(DrawableRectangle(0, 0, self.width-1, pixels-1)) # across the top
            self.image.draw(DrawableRectangle(0, 0, pixels-1, self.height-1)) # down the left
            self.image.draw(DrawableRectangle(self.width-pixels, 0, self.width-1, self.height-1)) # down the right
            self.image.draw(DrawableRectangle(0, self.height-pixels, self.width-1, self.height-1)) # across the bottom

    # Given filename or list of textlines, write text to image in fg color
    def text(
            self,
            input,              # a filename, or a list of text lines
            gravity = 'nw',     # one of nw, n, ne, w, c, e, sw, s, s.
            margin = 10,        # text margin
            wrap = False,       # wrap lines at right margin
            clip = None,        # clip text at margins
            point = 20,         # pointsize
            font = __font__     # font
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

        self.image.font(font)
        self.image.fontPointsize(point)
        tm = TypeMetric()
        self.image.fontTypeMetrics("M",tm)

        # x and y margins are based on gravity
        if gravity in ("nw","ne","w","e","sw","se"):
            xoffset = margin
        else:
            xoffset = 0

        if gravity in ("nw","n","ne"):
            yoffset = margin+tm.ascent()
        elif gravity in ("sw","s","se"):
            yoffset = margin-tm.descent()
        else:
            yoffset = 0

        maxcols = int((self.width-(margin*2)) // tm.textWidth())
        maxlines = int((self.height-(margin*2)) // (tm.textHeight()+1))

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

        dl = DrawableList()
        dl.append(DrawableGravity(self.gravities[gravity]))
        dl.append(DrawableText(xoffset, yoffset, _to_bytes('\n'.join(text))))
        self.image.draw(dl)

    # overlay image im at specified offset
    def overlay(self, im, pos=(0,0)):
        if type(pos) in [list, tuple]:
            pos=Geometry(pos)
        else:
            pos=self.gravities[pos]
        self.image.composite(im, pos, CompositeOperator.OverCompositeOp)

    # Load an image file and scale/stretch. Format is determined from data,
    # file extent, or leading "FMT:" tag (e.g "PNG:data")
    def read(
            self,
            filename,       # a filename, '-' for stdin
            margin=0,       # pixels to leave around edge of image
            stretch=False   # stretch image to fit image
        ):

        if filename == '-':
            try: fh = sys.stdin.buffer # python 3
            except: fh = sys.stdin     # python 2
        else:
            fh = open(filename, mode='rb')

        i=Image(Blob(fh.read()))
        g=Geometry(self.width-(margin*2), self.height-(margin*2))
        if stretch: g.aspect(True)
        i.scale(g)
        self.overlay(i,'c')

    # Write the image to a file or stdout. Format is determined from file
    # extent or leading "FMT:" tag (e.g "PNG:data").
    def write(self, filename):
        self.image.write(filename)

    # Return image raw RGB data)
    def rgb(self):
        blob=Blob()
        self.image.write(blob,"RGB",8)
        return blob.data
