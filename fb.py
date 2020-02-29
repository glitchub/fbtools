# python interface to fb.bin, works with python 2 or 3

from __future__ import print_function, division
import os
from ctypes import *

# directory containing this module also contains fb.bin
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

class framebuffer():
    # open indexed framebuffer and mmap it
    def __init__(self, device="/dev/fb0"):

        # we need fb.bin
        fb_bin = __here__+"/fb.bin"
        try:
            self.lib = CDLL(fb_bin)
        except Exception:
            print ("Unable to load %s\n"
                   "Most likely this is because you didn't build it.\n"
                   "Go to the fbtools directory and run 'make'." % fb_bin)
            quit(1)

        self.fbinfo = (c_uint*16)(); # too big is ok
        res = self.lib.fbopen(byref(self.fbinfo), _to_bytes(device))
        if res:
            raise Exception("fbopen %s failed (%d)" % (device, res))
        self.height = int(self.fbinfo[0])
        self.width = int(self.fbinfo[1])

    # write rgb data bytes to framebuffer
    def pack(self, rgb):
        pixels = len(rgb) // 3
        if self.lib.fbpack(byref(self.fbinfo), pixels, 0, rgb):
            raise Exception("fbpack %d pixels failed" % pixels)

    # get framebuffer to rgb data
    def unpack(self):
        pixels = self.width * self.height
        rgb = create_string_buffer(pixels * 3)
        if self.lib.fbunpack(byref(self.fbinfo), pixels, 0, rgb):
            raise Exception("fbunpack %d pixels failed" % pixels)
        return bytes(rgb)
