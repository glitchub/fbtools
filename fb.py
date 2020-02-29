# python interface to pgmagick and fb.bin, works with python 2 or 3

from __future__ import print_function, division
import os, sys
from ctypes import *
from pgmagick import *

# directory containing this module also contains fb.bin and needed fonts
__here__=os.path.dirname(__file__) or '.'

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

# create a frame buffer object which interfaces with library fb.bin
class framebuffer():
    # open indexed framebuffer and mmap it
    def __init__(self, device="/dev/fb0"):

        fb_bin=__here__+"/fb.bin"
        try:
            self.lib=CDLL(fb_bin)
        except Exception:
            print ("Unable to load %s\n"
                   "Most likely this is because you didn't build it.\n"
                   "Go to the fbtools directory and run 'make'." % fb_bin)
            quit(1)

        self.fbinfo=(c_uint*16)(); # too big is ok
        res=self.lib.fbopen(byref(self.fbinfo), _to_bytes(device))
        if res:
            raise Exception("fbopen %s failed (%d)" % (device, res))
        self.height=int(self.fbinfo[0])
        self.width=int(self.fbinfo[1])

    def pack(self, rgb):
        rgb=_to_bytes(rgb)
        pixels=len(rgb)//3
        if self.lib.fbpack(byref(self.fbinfo), pixels, 0, rgb):
            raise Exception("fbpack %d pixels failed" % pixels)

    def unpack(self, pixels):
        rgb=create_string_buffer(pixels*3)
        if self.lib.fbunpack(byref(self.fbinfo), pixels, 0, rgb):
            raise Exception("fbunpack %d pixels failed" % pixels)
        return _to_str(rgb)

# Clear framebuffer
# color: the color to fill
# device: the name of the frame buffer device
def fbclear(color="black", device="/dev/fb0"):
    fb=framebuffer(device)
    im=Image(Geometry(fb.width, fb.height), Color(color))
    blob=Blob()
    im.write(blob,"RGB",8)
    fb.pack(blob.data)

# Write image file to framebuffer. Most graphic images formats are supported
# (via imagemagick). If '-' then image is on stdin. Image will be scaled automatically to fit.
# margin: size in pixels of display margins
# stretch: if True, then aspect ratio is not maintained, image is stretch to fit completely within margins
# color: color of any unrendered background
# device: name of the frame buffer device
# debug,: if True, print some diagnostic info
def fbimage(image, margin=0, stretch=False, color="black", device="/dev/fb0", debug=False):

    if image == '-':
        try: fh = sys.stdin.buffer # python 3
        except: fh = sys.stdin     # python 2
    else:
        fh = open(image, mode='rb')

    # open framebuffer so we can get its geometry
    fb=framebuffer(device)
    if debug: print("frame buffer height=%d width=%d" % (fb.height, fb.width))

    # create background layer
    base=Image(Geometry(fb.width, fb.height), Color(color))
    base.fillColor(Color(color))
    base.strokeWidth(0)

    im=Image(Blob(fh.read()))
    if debug: print("original image height=%d width=%d" % (im.rows(), im.columns()))

    g=Geometry(fb.width-(margin*2), fb.height-(margin*2))
    if stretch: g.aspect(True)
    im.scale(g)
    if debug: print("scaled image height=%d width=%d" % (im.rows(), im.columns()))

    base.composite(im, GravityType.CenterGravity, CompositeOperator.OverCompositeOp)

    blob=Blob()
    base.write(blob,"RGB",8)
    fb.pack(blob.data)

# Display arbitrary text in frame buffer.
# input: a list of one or more lines of text, or the name of a text file ('-' for stdin)
# fg: text and border color.
# bg: background color.
# gravity: display alignment, one of "nw", "n", "ne", "w", "c", "e", "sw", "s", or "se"
# font: path to a ttf file, default is a monospaced sans-serif with Chinese characters
# margin: display edge to avoid
# border: width in pixels of screen border, in the fg color
# wrap: if True, wrap tjhe text to fit within margins, requires monospace font
# xtrim: if True, chop long lines to fit within horizontal margins, requires monospace font
# ytrim: if True, chop text lines to fit within vertical margins
# reference: font's widest character, required for wrap and xtrim
# device: name of the framebuffer device
# debug: print some debug data, don't set this
def fbtext(input, fg="White", bg="black", gravity='nw',point=20,
           font=__here__+"/WenQuanYiMicroHeiMono.ttf", device="/dev/fb0",
           margin=10, border=0, wrap=False, xtrim=False, ytrim=False,
           reference="M", debug=False):

    if type(input) is list:
        # clean up the list
        text = map(lambda s:_to_str(s).expandtabs(),input)
    else:
        if input == '-':
            try: fh = sys.stdin.buffer # python 3
            except: fh = sys.stdin     # python 2
        else:
            fh = open(input, mode='rb')

        text = map(lambda s:s.expandtabs(),_to_str(fh.read()).splitlines())

    fb = framebuffer(device)
    if debug: print("frame buffer height=%d width=%d" % (fb.height, fb.width))

    # create surface
    im = Image(Geometry(fb.width,fb.height),Color(bg or "black"))
    im.fillColor(Color(fg or "white"))
    im.strokeWidth(0)
    im.font(font)
    im.fontPointsize(point)

    if border == 1:
        im.draw(DrawableLine(0, 0, fb.width-1, 0)) # across the top
        im.draw(DrawableLine(0, 0, 0, fb.height-1)) # down the left
        im.draw(DrawableLine(fb.width-1, 0, fb.width-1, fb.height-1)) # down the right
        im.draw(DrawableLine(0, fb.height-1, fb.width-1, fb.height-1)) # across the bottom
    elif border > 0:
        im.draw(DrawableRectangle(0, 0, fb.width-1, border-1)) # across the top
        im.draw(DrawableRectangle(0, 0, border-1, fb.height-1)) # down the left
        im.draw(DrawableRectangle(fb.width-border, 0, fb.width-1, fb.height-1)) # down the right
        im.draw(DrawableRectangle(0, fb.height-border, fb.width-1, fb.height-1)) # across the bottom

    margin += border

    # get font info
    tm = TypeMetric()
    im.fontTypeMetrics(reference,tm)
    if debug:
        print("reference char '%s': ascent=%d descent=%d textheight=%d textwidth=%d maxadvance=%d" %
            (reference, tm.ascent(),tm.descent(),tm.textHeight(),tm.textWidth(), tm.maxHorizontalAdvance()))

    # x and y margins are based on gravity
    if gravity in ("nw","ne","w","e","sw","se"):
        xoffset = margin
    else:
        xoffset = 0

    if gravity in ("nw","n","ne"):
        yoffset = margin+tm.ascent()
    elif gravity in ("sw","s","se"):
        yoffset = margin+(-tm.descent())
    else:
        yoffset=0

    maxcols = int((fb.width-(margin*2))//tm.textWidth())
    maxlines = int((fb.height-(margin*2))//(tm.textHeight()+1))
    if debug: print("xoffset=%d yoffset=%d maxcols=%d maxlines=%d" % (xoffset, yoffset, maxcols, maxlines))

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

    if ytrim:
        text = text[:maxlines]

    if xtrim:
        text = map(lambda s:s[:maxcols],text)

    if debug: print('\n'.join(text))

    dl = DrawableList()
    dl.append(DrawableGravity({"nw": GravityType.NorthWestGravity,
                               "n":  GravityType.NorthGravity,
                               "ne": GravityType.NorthEastGravity,
                               "w":  GravityType.WestGravity,
                               "c":  GravityType.CenterGravity,
                               "e":  GravityType.EastGravity,
                               "sw": GravityType.SouthWestGravity,
                               "s":  GravityType.SouthGravity,
                               "se": GravityType.SouthEastGravity}[gravity]))
    dl.append(DrawableText(xoffset, yoffset, _to_bytes('\n'.join(text))))
    im.draw(dl)

    blob = Blob()
    im.write(blob,"RGB",8)
    fb.pack(blob.data)
