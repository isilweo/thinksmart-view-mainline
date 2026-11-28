#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Replace biquad coefficients in a TAS5782M register-pair DSP blob.

The blob is a flat stream of (register, value) byte pairs: register 0x00
selects the page, register 0x7f on page 0 selects the book. Coefficients
are 32-bit big-endian words, written one byte per register.

Usage: tas5782m-eq-patch.py IN OUT BOOK:PAGE:REG=W0,W1,W2,W3,W4 ...
  e.g. 8c:16:30=7fffffff,00000000,00000000,00000000,00000000

Only registers that the blob already writes are changed (the blob layout
stays the same), and every requested byte must be found exactly once.
"""
import sys


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    data = bytearray(open(sys.argv[1], "rb").read())
    want = {}
    for spec in sys.argv[3:]:
        addr, words = spec.split("=")
        book, page, reg = (int(x, 16) for x in addr.split(":"))
        for i, w in enumerate(words.split(",")):
            w = int(w, 16)
            for j in range(4):
                key = (book, page, reg + 4 * i + j)
                want[key] = (w >> (24 - 8 * j)) & 0xff
    seen = {k: 0 for k in want}
    book = page = 0
    for i in range(0, len(data) - 1, 2):
        r, v = data[i], data[i + 1]
        if r == 0x00:
            page = v
            continue
        if r == 0x7f and page == 0:
            book = v
            continue
        key = (book, page, r)
        if key in want:
            data[i + 1] = want[key]
            seen[key] += 1
    bad = {k: n for k, n in seen.items() if n != 1}
    if bad:
        sys.exit("not written exactly once: " + ", ".join(
            "%02x:%02x:%02x x%d" % (k + (n,)) for k, n in sorted(bad.items())))
    open(sys.argv[2], "wb").write(data)
    print("%d bytes changed in %d registers" % (
        sum(1 for k in want), len(want)))


if __name__ == "__main__":
    main()
