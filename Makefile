CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -Wpedantic
PYTHON ?= python3

.PHONY: all test demo clean
all: line-ending-check

line-ending-check: line-ending-check.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -std=c17 $(LDFLAGS) -o $@ $< $(LDLIBS)

test: line-ending-check
	$(PYTHON) -m unittest -v test_line_ending_check.py

demo: line-ending-check
	printf 'alpha\nbeta\r\ngamma\rdelta\n' | ./line-ending-check -

clean:
	rm -f line-ending-check
