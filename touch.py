# module to provide touch screen support
from __future__ import print_function
import os, sys, glob, fcntl, struct, select, time
from ctypes import *

# python2 doesn't support monotonic time, use the wall clock for timeouts
if 'monotonic' not in dir(time): time.monotonic=time.time

# See linux/input.h for more information

# Returned by EVIOCGABS ioctl
class input_absinfo(Structure):
    _fields_ = [
        ("value", c_uint),        # last value returned
        ("minimum", c_uint),      # minimum value for the axis
        ("maximum", c_uint),      # maximum value for the axis
        ("fuzz", c_uint),         # fuzz value used to filter values from the input stream
        ("flat", c_uint),         # indicates joystick discard
        ("resolution", c_uint),   # units/mm
    ]

# ioctls to retrieve X and Y axis information
EVIOCGABS_X = 0x80184540
EVIOCGABS_Y = 0x80184541

class touch():
    def __init__(self, width, height):
        # Locate EV_ABS device with correct X and Y dimensions, return with
        # the device handle held open
        for device in glob.glob("/dev/input/event*"):
            fd = open(device, 'rb')
            try:
                # try to read absinfo for x and y axis
                x_info = input_absinfo()
                fcntl.ioctl(fd, EVIOCGABS_X, x_info, True)
                if x_info.minimum == 0 and x_info.maximum == width:
                    y_info = input_absinfo()
                    fcntl.ioctl(fd, EVIOCGABS_X, y_info, True)
                    if y_info.minimum == 0 and y_info.maximum == height:
                        fd.close()
                        # found a usable device
                        self.device = device
                        self.width = width
                        self.height = height
                        self.fd = None
                        return
            except OSError:
                # ioctl not supported
                pass
            fd.close()
        raise Exception("No touch device found")

    # Return touch (x, y) or None if timeout
    # Event packets from device are 16 bytes in form:
    #     struct input_event {
    #        struct timeval time;
    #        __u16 type;
    #        __u16 code;
    #        __s32 value;
    #     };
    # See linux/input.h
    def position(self, timeout=None, flush=False):
        while True:
            if self.fd is None:
                self.fd = open(self.device, 'rb')

            while flush:
                s = select.select([self.fd],[],[],0)
                if not s[0]: break
                self.fd.read(16)

            expire = None
            press = x_abs = y_abs = None

            while True:

                if timeout is not None:
                    if not expire: expire = time.monotonic() + timeout
                    s = select.select([self.fd],[],[], max(0, expire-time.monotonic()))
                    if not s[0]: return None

                time, type, code, value = struct.unpack("IHHI", self.fd.read(16))

                if type == 0:
                    if press and x_abs is not None and y_abs is not None: return (x_abs, y_abs)
                    press = x_abs = y_abs = None
                elif type == 1 and code == 330 and value == 1:
                    press = True
                elif type == 3 and code == 0:
                    x_abs = value
                elif type == 3 and code == 1:
                    y_abs = value
