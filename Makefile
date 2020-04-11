PYTHON = fbcap  fbclear  fbdialog  fbimage  fbmenu  fb.py  fbquery  fbscreen.py  fbtext touch.py

CFLAGS += -s -O3

fb.bin: fb.o
	gcc ${CFLAGS} -shared -Wl,-soname,$@ -o $@ $<
	chmod 644 $@

.INTERMEDIATE: fb.o
fb.o: fb.c; gcc ${CFLAGS} -c -fPIC -o $@ $<

.PHONY: clean
clean:; rm -rf fb.bin *.o *.pyc __pycache__

.PHONY: lint
lint:; pylint3 -E -dno-member ${PYTHON}
