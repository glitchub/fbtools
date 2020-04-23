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

# ioctl to retrieve supported keys
EVIOCGBIT_EVKEY_96 = 0x80604521

# Button events of interest
BTN_MOUSE = 0x110
BTN_TOUCH = 0x14a
BTN_STYLUS = 0x14b

# In order of preference
buttons = (BTN_TOUCH, BTN_STYLUS, BTN_MOUSE)

class Touch():
    def __init__(self, width=None, height=None, device=None):
        # Locate EV_ABS device with correct X and Y dimensions, return with
        # the device handle held open
        for td in glob.glob(device if device else "/dev/input/event*"):
            fd = open(td, 'rb')
            try:
                # get absinfo for x and y axis
                x = input_absinfo()
                fcntl.ioctl(fd, EVIOCGABS_X, x, True)
                y = input_absinfo()
                fcntl.ioctl(fd, EVIOCGABS_Y, y, True)
                # get array of supported keys
                keys = (c_ubyte * 96)()
                fcntl.ioctl(fd, EVIOCGBIT_EVKEY_96, keys, True)
                if x.minimum == 0 and (x.maximum == width if width else x.maximum >= 64):
                    if y.minimum == 0 and (y.maximum == height if height else y.maximum >= 64):
                        for button in buttons:
                            if keys[button//8] & (1 << (button & 7)):
                                # found a usable device
                                self.fd = None
                                self.device = td
                                self.button = button
                                self.width = x.maximum
                                self.height = y.maximum
                                self.scale_width = None  # these can be set later to scale the results
                                self.scale_height = None
                                return
            except OSError:
                # ioctl not supported so advance to next
                pass
            fd.close()
        raise Exception("No touch device found")

    # Return (x, y) on touch or None on release
    # If timeout given, return False after timeout seconds
    # If reset given, close and reopen the device
    def touch(self, timeout=None, reset=False):
        if reset and self.fd is not None:
            self.fd.close()
            self.fd = None

        if timeout is not None:
            if timeout <= 0: return False
            timeout += time.monotonic()

        if self.fd is None:
            self.fd = open(self.device, 'rb')
            os.set_blocking(self.fd.fileno(), False)

        press = xabs = yabs = None

        while True:
            # It looks like some touch drivers don't support the poll method
            # correctly? So first try to read a packet in non-blocking mode and
            # select only if nothing is waiting.
            while True:
                packet = self.fd.read(16)
                if packet:
                    if len(packet) == 16: break
                    # Partial packet, maybe the rest is in the pipe?
                    for x in range(10):
                        os.sched_yield()
                        packet += self.fd.read(16-len(packet))
                        if len(packet) == 16: break
                    # Ugh, ignore partial packet
                else:
                    s = select.select([self.fd], [], [], max(0, timeout-time.monotonic()) if timeout else None)
                    if not s[0]: return False # Timeout!

            # An event packet is 16 bytes:
            #     struct input_event {
            #        struct timeval time; // 8 bytes
            #        __u16 type;
            #        __u16 code;
            #        __s32 value;
            #     };
            # We ignore the time
            type, code, value = struct.unpack("8xHHi", packet)

            if type == 0: # EV_SYN
                if press == 1:
                    if xabs is not None and yabs is not None:
                        # scale if enabled
                        if self.scale_width: xabs = int(xabs * (self.scale_width/self.width))
                        if self.scale_height: yabs = int(yabs * (self.scale_height/self.height))
                        return (xabs, yabs)
                elif press == 0:
                    return None
                press = xabs = yabs = None
            elif type == 1 and code == self.button: # EV_KEY and our button
                press = value
            elif type == 3 and code == 0:           # EV_ABS and ABS_X
                xabs = value
            elif type == 3 and code == 1:           # EV_ABS and ABS_Y
                yabs = value

    # Return true when touch is released, or false on timeout
    def release(self, timeout=None):
        if timeout: timeout += time.monotonic()
        while True:
            xy = self.touch(timeout = max(0, timeout-time.monotonic()) if timeout else None)
            if xy is None: return True      # release
            if xy is False: return False    # timeout

    # Given dict of {box:value}, where 'box' defines an area in form [x1, y1,
    # x2, y2], look for a touch in one of the boxes, and return the
    # corresponding value. Boxes must not overlap.
    def select(self, boxes, timeout=None):
        if timeout: timeout += time.monotonic()
        while True:
            xy = self.touch(timeout = max(0, timeout-time.monotonic()) if timeout else None)
            if xy is False: return False    # timeout
            if xy:
                for box, value in boxes.items():
                    if xy[0] >= box[0] and xy[0] <= box[2] and xy[1] >= box[1] and xy[1] <= box[3]:
                        return value

if __name__ == "__main__":
    t = Touch() # Find the first EV_ABS device with X and Y axis and a usable touch button
    print("Using device %s, %d x %d, key code %d" % (t.device, t.width, t.height, t.button))
    # scale it to virtual 250x250 screen
    t.scale_width=250
    t.scale_height=250
    while True:
        pos = t.touch(timeout=5)
        if pos : print("%d x %d" % pos)
        elif pos is None: print("Release")
        else: print("Timeout")
