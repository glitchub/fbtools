PROGRAMS = fbquery fbget fbput

CFLAGS += -s -O3

default: ${PROGRAMS} fb.bin

${PROGRAMS}: % : %.c fb.o

fb.bin: fb.o; gcc ${CFLAGS} -shared -Wl,-soname,$@ -o $@ $<

.INTERMEDIATE: fb.o  
fb.o: fb.c; gcc ${CFLAGS} -c -fPIC -o $@ $<

clean:; rm -f ${PROGRAMS} fb.bin fb.pyc fb.o
