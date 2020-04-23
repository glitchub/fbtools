.PHONY: default
default: fb.bin

# create shared library
CFLAGS += -s -O3
fb.bin: fb.o
	gcc ${CFLAGS} -shared -Wl,-soname,$@ -o $@ $<
	chmod 644 $@

.INTERMEDIATE: fb.o
fb.o: fb.c; gcc ${CFLAGS} -c -fPIC -o $@ $<

.PHONY: clean
clean:; rm -rf fb.bin *.o *.pyc __pycache__

.PHONY: lint
lint:; pylint3 -E -dno-member *.py fbcap fbclear fbdialog fbimage fbmenu fbquery fbtext

# install and uninstall requires root
ifeq (${USER},root)
site := $(shell python3 -c'import site; print(site.getsitepackages()[0])')
ifeq ($(strip ${site}),)
$(error Unable to get python package directory)
endif

# pre-compile modules and symlink this directory as a package
.PHONY: install
install: fb.bin
	rm -rf __pycache__
	py3compile *.py
	ln -sf ${CURDIR} ${site}

# delete package symlink
.PHONY: uninstall
uninstall: clean; rm -f ${site}/$(notdir ${CURDIR})

endif
