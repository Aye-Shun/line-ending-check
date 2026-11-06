#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

struct counts {
    uintmax_t lf;
    uintmax_t crlf;
    uintmax_t cr;
    bool has_bytes;
};

enum scan_result { SCAN_OK, SCAN_BINARY, SCAN_ERROR };

static enum scan_result scan(FILE *input, struct counts *counts)
{
    unsigned char buffer[4096];
    bool pending_cr = false;
    size_t length;

    while ((length = fread(buffer, 1, sizeof buffer, input)) != 0) {
        counts->has_bytes = true;
        for (size_t i = 0; i < length; ++i) {
            unsigned char byte = buffer[i];
            if (byte == '\0') {
                return SCAN_BINARY;
            }
            if (pending_cr) {
                pending_cr = false;
                if (byte == '\n') {
                    ++counts->crlf;
                    continue;
                }
                ++counts->cr;
            }
            if (byte == '\r') {
                pending_cr = true;
            } else if (byte == '\n') {
                ++counts->lf;
            }
        }
    }

    if (ferror(input)) {
        return SCAN_ERROR;
    }
    if (pending_cr) {
        ++counts->cr;
    }
    return SCAN_OK;
}

static const char *style(const struct counts *counts)
{
    if (!counts->has_bytes) {
        return "empty";
    }
    unsigned kinds = (counts->lf != 0) + (counts->crlf != 0) + (counts->cr != 0);
    if (kinds > 1) {
        return "mixed";
    }
    if (counts->crlf) {
        return "CRLF";
    }
    if (counts->lf) {
        return "LF";
    }
    if (counts->cr) {
        return "CR";
    }
    return "no line endings";
}

int main(int argc, char **argv)
{
    const char *usage = "Usage: line-ending-check FILE | -";
    if (argc != 2) {
        fprintf(stderr, "%s\n", usage);
        return 2;
    }
    if (strcmp(argv[1], "--help") == 0) {
        puts(usage);
        puts("Count LF, CRLF, and lone CR bytes. Use - to read standard input.");
        return fflush(stdout) == EOF ? 1 : 0;
    }

    bool from_stdin = strcmp(argv[1], "-") == 0;
    FILE *input = from_stdin ? stdin : fopen(argv[1], "rb");
    if (input == NULL) {
        perror("line-ending-check: open input");
        return 1;
    }

    struct counts counts = {0};
    enum scan_result result = scan(input, &counts);
    if (!from_stdin && fclose(input) == EOF && result == SCAN_OK) {
        result = SCAN_ERROR;
    }
    if (result == SCAN_BINARY) {
        fputs("line-ending-check: NUL byte found (possible binary input)\n", stderr);
        return 1;
    }
    if (result == SCAN_ERROR) {
        fputs("line-ending-check: could not read or close input\n", stderr);
        return 1;
    }

    if (printf("Style: %s\nLF: %" PRIuMAX "\nCRLF: %" PRIuMAX "\nCR: %" PRIuMAX "\n",
               style(&counts), counts.lf, counts.crlf, counts.cr) < 0 ||
        fflush(stdout) == EOF) {
        fputs("line-ending-check: could not write report\n", stderr);
        return 1;
    }
    return 0;
}
