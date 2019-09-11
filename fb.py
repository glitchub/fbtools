#!/usr/bin/python2

import os, sys
from ctypes import * 

class framebuffer(object):
    # open indexed framebuffer and mmap it
    def __init__(self, device="/dev/fb0"):
        
        fb_bin=sys.path[0]+"/fb.bin"
        try:
            self.lib=CDLL(fb_bin)
        except Exception:
            print ("Unable to load %s\n"
                   "Most likely this is because you didn't build it.\n"
                   "Go to the fbtools directory and run 'make'." % fb_bin)
            quit(1)

        self.fbinfo=(c_uint*16)(); # too big is ok
        res=self.lib.fbopen(byref(self.fbinfo), device)
        if res: 
            raise Exception("fbopen %s failed (%d)" % (device, res))
        self.height=int(self.fbinfo[0])
        self.width=int(self.fbinfo[1])

    def pack(self, rgb):
        pixels=len(rgb)/3
        if self.lib.fbpack(byref(self.fbinfo), pixels, 0, rgb): 
            raise Exception("fbpack %d pixels failed" % pixels)

    def unpack(self, rgb):
        pixels=len(rgb)/3
        if self.lib.fbunpack(byref(self.fbinfo), pixels, 0, rgb): 
            raise Exception("fbunpack %d pixels failed" % pixels)
