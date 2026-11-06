# Line Ending Check

A small C command-line tool that counts LF, CRLF, and lone CR in a file. It helps identify mixed line endings before an editor or formatter changes them.

## Try it

Build with a C17 compiler and Make on macOS or Linux:

```sh
make
./line-ending-check notes.txt
printf 'alpha\nbeta\r\ngamma\rdelta\n' | ./line-ending-check -
```

The example reports a mixed style with two LF, one CRLF, and one CR. Run `make demo` to generate those same bytes and inspect them. An empty file and a file with no line endings have separate labels.

The scanner keeps one pending CR between reads so a CRLF pair still counts together when it spans two buffers. A trailing CR counts on its own. The tool reads bytes and leaves the input unchanged.

A NUL byte stops the scan as possible binary input. This check cannot recognize every binary file, and UTF-16 text with NUL bytes is rejected. A successful scan exits 0 even for mixed endings. Input or output errors exit 1, and incorrect argument counts exit 2.

Run `make test` with Python 3 for file, stdin, boundary, and error checks.
