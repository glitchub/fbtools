# python interface to fb.bin
import os
from ctypes import *

# directory that contains this module must also contain fb.bin
_fb_bin=(os.path.dirname(__file__) or '.')+"/fb.bin"
if not os.path.isfile(_fb_bin):
    raise Exception("Can't find %s\n"
        "Most likely this is because you didn't build it.\n"
        "Go to the fbtools directory and run 'make'." % _fb_bin)

class Framebuffer():
    # open indexed framebuffer and mmap it
    def __init__(self, device=None):
        if not device: device = "/dev/fb0"
        self.lib = CDLL(_fb_bin)
        self.fbinfo = (c_uint*8)();
        res = self.lib.fbopen(byref(self.fbinfo), bytes(device, 'utf-8'))
        if res: raise Exception("fbopen %s failed (%d)" % (device, res))
        self.height = int(self.fbinfo[0])   # height in pixels
        self.width = int(self.fbinfo[1])    # width in pixels
        self.bpp = int(self.fbinfo[2])      # bytes per pixel, can be 2, 3 or 4. If 2 then colorspace is 565.
        self.red = int(self.fbinfo[3])      # bit offset of red in the pixel
        self.green = int(self.fbinfo[4])    # bit offset of green in the pixel
        self.blue = int(self.fbinfo[5])     # bit offset of red in the pixel

    # Write rgb data to framebuffer. Note rgb must be height*width*3, but only
    # the area designated by left,top to right,bottom will be updated.
    def pack(self, rgb, left=0, top=0, right=None, bottom=None):
        if right is None: right = self.width - 1
        if bottom is None: bottom = self.height - 1
        assert (len(rgb) == self.height * self.width * 3) and (0 <= left <= right < self.width) and (0 <= top <= bottom < self.height)
        if self.lib.fbpack(byref(self.fbinfo), rgb, left, top, right, bottom): raise Exception("fbpack failed")

    # get framebuffer to rgb data
    def unpack(self):
        rgb = create_string_buffer(self.height * self.width * 3)
        if self.lib.fbunpack(byref(self.fbinfo), rgb): raise Exception("fbunpack failed")
        return bytes(rgb)
