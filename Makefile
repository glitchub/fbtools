PYTHON = fbcap fbclear fbdialog fbimage fbmenu fb.py fbquery fbtext screen.py touch.py

CFLAGS += -s -O3

# create shared library
fb.bin: fb.o
	gcc ${CFLAGS} -shared -Wl,-soname,$@ -o $@ $<
	chmod 644 $@

.INTERMEDIATE: fb.o
fb.o: fb.c; gcc ${CFLAGS} -c -fPIC -o $@ $<

# symlink this directory as a package, note avoid use of ${PWD} with sudo
site := $(shell python3 -c'import site; print(site.getsitepackages()[0])')
link := ${site}/$(notdir ${CURDIR})
.PHONY: install
install:
ifneq (${site},)
	mkdir -p ${site}
	ln -sf ${CURDIR} ${link}
endif

# clean files
.PHONY: clean
clean:; rm -rf fb.bin *.o *.pyc __pycache__

# clean and delete package symlink
.PHONY: uninstall
uninstall: clean;
ifneq (${site},)
	rm -f ${link}
endif

.PHONY: lint
lint:; pylint3 -E -dno-member ${PYTHON}
