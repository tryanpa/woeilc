#!/usr/bin/env python3
"""Convert a 32x32 PNG portrait into DATA lines for woeilc.bas.

Usage: python3 tools/face.py art/merchant.png [--first-line 1400]
                              [--ink 2] [--paper 12] [--preview out.png]

The picture must be exactly 32x32. Dark opaque pixels are ink, everything
else is paper. Each 8x8 block becomes one TI character pattern; identical
blocks are stored once. All blocks of a face share one colour pair (ink on
paper), which is what the TI's colour sets allow.

Output, as DATA lines to paste into woeilc.bas:
  ink colour, paper colour, number of unique blocks
  the unique block patterns as 16 hex digits each
  four row strings of four letters: A is the first unique block, B the next,
  and so on. The game turns letter L into character code ASC(L)+31.
"""
import argparse
import sys

from PIL import Image


def tiles_of(path):
    im = Image.open(path).convert('RGBA')
    if im.size != (32, 32):
        sys.exit('%s is %dx%d, expected 32x32' % (path, im.size[0], im.size[1]))
    px = im.load()
    ink = [[1 if px[x, y][3] > 128 and sum(px[x, y][:3]) < 384 else 0
            for x in range(32)] for y in range(32)]
    rows = []
    for ty in range(4):
        row = []
        for tx in range(4):
            bits = tuple(tuple(ink[ty * 8 + y][tx * 8 + x] for x in range(8)) for y in range(8))
            row.append(bits)
        rows.append(row)
    return ink, rows


def hexof(bits):
    return ''.join('%02X' % int(''.join(map(str, r)), 2) for r in bits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('png')
    ap.add_argument('--first-line', type=int, default=1400)
    ap.add_argument('--ink', type=int, default=2)
    ap.add_argument('--paper', type=int, default=12)
    ap.add_argument('--preview')
    a = ap.parse_args()

    ink, rows = tiles_of(a.png)
    unique = []
    letters = []
    for row in rows:
        s = ''
        for t in row:
            if t not in unique:
                unique.append(t)
            s += chr(65 + unique.index(t))
        letters.append(s)
    if len(unique) > 16:
        sys.exit('needs %d unique blocks, the limit is 16' % len(unique))

    n = a.first_line
    out = ['%d DATA %d,%d,%d' % (n, a.ink, a.paper, len(unique))]
    pats = ['"%s"' % hexof(t) for t in unique]
    for i in range(0, len(pats), 4):
        n += 1
        out.append('%d DATA %s' % (n, ','.join(pats[i:i + 4])))
    n += 1
    out.append('%d DATA %s' % (n, ','.join('"%s"' % s for s in letters)))
    print('\n'.join(out))
    print('%d unique blocks of 16' % len(unique), file=sys.stderr)

    if a.preview:
        pal = {1: (0, 0, 0), 2: (0, 0, 0), 3: (33, 200, 66), 4: (94, 220, 120), 5: (84, 85, 237),
               6: (125, 118, 252), 7: (212, 82, 77), 8: (66, 235, 245), 9: (252, 85, 84),
               10: (255, 121, 120), 11: (212, 193, 84), 12: (230, 206, 128), 13: (33, 176, 59),
               14: (201, 91, 186), 15: (204, 204, 204), 16: (255, 255, 255)}
        im = Image.new('RGB', (32, 32), pal[a.paper])
        p = im.load()
        for y in range(32):
            for x in range(32):
                if ink[y][x]:
                    p[x, y] = pal[a.ink]
        im.resize((256, 256), Image.NEAREST).save(a.preview)


if __name__ == '__main__':
    main()
