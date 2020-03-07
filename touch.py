# module to provide touch screen support
import os, sys, glob, fcntl, struct, select, time
from ctypes import *

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
    def __init__(self, width=None, height=None):
        # Locate EV_ABS device with correct X and Y dimensions, return with
        # the device handle held open
        for device in glob.glob("/dev/input/event*"):
            fd = open(device, 'rb')
            try:
                # try to read absinfo for x and y axis
                x = input_absinfo()
                fcntl.ioctl(fd, EVIOCGABS_X, x, True)
                if x.minimum == 0 and (x.maximum == width if width else x.maximum > 64):
                    y = input_absinfo()
                    fcntl.ioctl(fd, EVIOCGABS_Y, y, True)
                    if y.minimum == 0 and (y.maximum == height if height else y.maximum > 64):
                        fd.close()
                        # found a usable device
                        self.device = device
                        self.width = x.maximum
                        self.height = y.maximum
                        self.fd = None
                        return
            except OSError:
                # ioctl not supported, advance to next
                pass
            fd.close()
        raise Exception("No touch device found")

    # Return (x, y) on touch or None on release
    # If timeout, return False after timeout seconds
    # If reset, close and reopen then device
    def position(self, timeout=None, reset=False, release=False):
        while True:
            if reset and self.fd is not None:
                self.fd.close()
                self.fd = None

            if timeout is not None:
                if timeout <= 0: return False
                timeout += time.monotonic()

            if self.fd is None:
                self.fd = open(self.device, 'rb')

            press = xabs = yabs = None

            while True:

                if timeout:
                    s = select.select([self.fd],[],[], max(0, timeout-time.monotonic()))
                    if not s[0]: return False

                # Event packets device are 16 bytes in form:
                #     struct input_event {
                #        struct timeval time;
                #        __u16 type;
                #        __u16 code;
                #        __s32 value;
                #     };
                # We ignore the timestamps.
                type, code, value = struct.unpack("8xHHi", self.fd.read(16))

                if type == 0:
                    if press == 1:
                        if xabs is not None and yabs is not None: return (x_abs, y_abs)
                    elif press == 0:
                        return None
                    press = xabs = yabs = None
                elif type == 1 and code == 330:
                    press = value
                elif type == 3 and code == 0:
                    xabs = value
                elif type == 3 and code == 1:
                    yabs = value

    # Given dict of box:value, return value for a touch within the box. A box
    # defines an area in form [x1, y1, x2, y2].
    def boxes(self, boxes, timeout=None):
        if timeout is not None:
            timeout += time.monotonic()

        while True:
            remain = None
            if timeout:
                remain=time.monotonic-timeout
                if remain <= 0: return None
            xy = self.position(timeout=remain)
            if xy is None: return None
            for box, value in boxes.items():
                if xy[0] >= box[0] and xy[0] <= box[2] and xy[1] >= box[1] and xy[1] <= box[3]:
                    return value

if __name__ == "__main__":
    t = touch() # without arguments, find first EV_ABS device with X and Y axis
    print("Using device %s, %d x %d" % (t.device, t.width, t.height))
    while True:
        pos = t.position(timeout=5, release=True)
        if pos is False: print("Timeout")
        elif pos is None: print("Release")
        else: print("Touch at %d x %d" % pos)
