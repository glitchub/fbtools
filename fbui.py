import os, sys, fb, screen, touch
from pgmagick import *

class button():
    def __init__(self, screen, text, left, top, right, bottom, fg=None, bg=None):
        self.screen = screen
        self.layer = screen.text(text, left, top, right, bottom, gravity="center", bg=bg, fg=fg, commit=False)
        self.released()

    # Add "button pressed" border
    def pressed(self):
        self.layer.img.strokeWidth(1)
        self.layer.img.strokeColor("#444")
        self.layer.img.draw(DrawableLine(0, 0, self.layer.width-1, 0))
        self.layer.img.draw(DrawableLine(0, 0, 0, self.layer.height-1))
        self.layer.img.strokeColor("#CCC")
        self.layer.img.draw(DrawableLine(0, self.layer.height-1, self.layer.width-1, self.layer.height-1))
        self.layer.img.draw(DrawableLine(self.layer.width-1, 0, self.layer.width-1, self.layer.height-1))
        self.screen.merge(self.layer)

    # Add "button released" border
    def released(self):
        self.layer.img.strokeWidth(1)
        self.layer.img.strokeColor("#CCC")
        self.layer.img.draw(DrawableLine(0, 0, self.layer.width-1, 0))
        self.layer.img.draw(DrawableLine(0, 0, 0, self.layer.height-1))
        self.layer.img.strokeColor("#444")
        self.layer.img.draw(DrawableLine(0, self.layer.height-1, self.layer.width-1, self.layer.height-1))
        self.layer.img.draw(DrawableLine(self.layer.width-1, 0, self.layer.width-1, self.layer.height-1))
        self.screen.merge(self.layer)

class ui():
    def __init__(self, fbdev="/dev/fb0", touchdev=None):
        self.fb = fb.framebuffer(device=fbdev)
        self.screen = screen.screen(self.fb.width, self.fb.height)
        self.screen.border()
        self.touch = touch.touch(self.fb.width, self.fb.height, device=touchdev)

    def update(self):
        self.fb.pack(self.screen.rgb)

    def ask(self, question="Please select Yes or No", yestext="Yes", notext="No", yescolor="green", nocolor="red"):
        textbox = self.screen.box(10, 10, 90, 55)
        yesbox =  self.screen.box(20, 60, 45, 80)
        nobox =   self.screen.box(55, 60, 80, 80)
        self.screen.text(question, *textbox, gravity='center')
        yes = button(self.screen, yestext, *yesbox, bg=yescolor)
        no = button(self.screen, notext, *nobox, bg=nocolor)
        self.update()
        selection = self.touch.select({yesbox:True, nobox:False})
        yes.pressed() if selection else no.pressed()
        self.update();
        self.touch.release()
        yes.released() if selection else no.released()
        self.update();
        return selection
