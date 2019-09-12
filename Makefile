GENERATE=fb.bin fbquery fbget fbput
default: $(GENERATE)

fb.bin: fb.o; gcc -shared -Wl,-soname,$@ -o $@ $<

fbput fbquery fbget: % : %.c fb.o

.INTERMEDIATE: fb.o  
fb.o: fb.c; gcc -c -fPIC -o $@ $<

clean:; rm -f $(GENERATE) fb.pyc fb.o
