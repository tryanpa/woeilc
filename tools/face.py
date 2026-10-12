#!/usr/bin/env python3
"""Turn a cast list of 32x32 portraits into DATA lines for woeilc.bas.

Usage: python3 tools/face.py art/cast.txt [--first-line 1400]
                              [--ink 2] [--paper 12] [--preview sheet.png]

The cast list has one face per line, "png | caption", and # starts a comment.
Each picture must be exactly 32x32, black ink on a transparent background.
Dark opaque pixels are ink and everything else is paper.

Every face is stored as 16 character patterns, four rows of four. A row is
one DATA string of 64 hex digits, which the game loads with a single
CALL CHAR (CALL CHAR defines at most four characters per call). All faces
share one slot of 16 characters, so the size of the cast does not change how
many characters the game uses.

Output, as DATA lines to paste into woeilc.bas:
  ink colour, paper colour, number of faces
  per face: the caption, then its four row strings
"""
import argparse
import os
import sys

from PIL import Image

PAL = {2: (0, 0, 0), 3: (33, 200, 66), 4: (94, 220, 120), 5: (84, 85, 237),
       6: (125, 118, 252), 7: (212, 82, 77), 8: (66, 235, 245), 9: (252, 85, 84),
       10: (255, 121, 120), 11: (212, 193, 84), 12: (230, 206, 128), 13: (33, 176, 59),
       14: (201, 91, 186), 15: (204, 204, 204), 16: (255, 255, 255)}


def read_ink(path):
    im = Image.open(path).convert('RGBA')
    if im.size != (32, 32):
        sys.exit('%s is %dx%d, expected 32x32' % (path, im.size[0], im.size[1]))
    px = im.load()
    ink = []
    for y in range(32):
        row = []
        for x in range(32):
            r, g, b, a = px[x, y]
            if a > 128 and r + g + b < 384:
                row.append(1)
            else:
                if a > 128 and (r, g, b) != (255, 255, 255) and r + g + b >= 384 and abs(r - g) + abs(g - b) > 40:
                    print('warning: %s has a coloured pixel at (%d,%d); treated as paper' % (path, x, y),
                          file=sys.stderr)
                row.append(0)
        ink.append(row)
    return ink


def rows_hex(ink):
    out = []
    for ty in range(4):
        s = ''
        for tx in range(4):
            for y in range(8):
                bits = ''.join(str(ink[ty * 8 + y][tx * 8 + x]) for x in range(8))
                s += '%02X' % int(bits, 2)
        out.append(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cast')
    ap.add_argument('--first-line', type=int, default=1400)
    ap.add_argument('--ink', type=int, default=2)
    ap.add_argument('--paper', type=int, default=12)
    ap.add_argument('--preview')
    a = ap.parse_args()

    base = os.path.dirname(os.path.abspath(a.cast))
    faces = []
    for raw in open(a.cast):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        path, _, caption = [p.strip() for p in line.partition('|')]
        if not caption:
            sys.exit('no caption for %s' % path)
        if len(caption) > 22:
            sys.exit('caption "%s" is %d characters, the limit is 22' % (caption, len(caption)))
        if '"' in caption:
            sys.exit('caption "%s" contains a quote mark' % caption)
        full = path if os.path.isabs(path) else os.path.join(os.path.dirname(base), path)
        if not os.path.exists(full):
            full = os.path.join(base, os.path.basename(path))
        faces.append((caption.upper(), read_ink(full)))

    if not 3 <= len(faces) <= 12:
        sys.exit('the cast needs 3 to 12 faces, found %d' % len(faces))
    n = a.first_line
    out = ['%d DATA %d,%d,%d' % (n, a.ink, a.paper, len(faces))]
    for caption, ink in faces:
        n += 1
        out.append('%d DATA "%s"' % (n, caption))
        for r in rows_hex(ink):
            n += 1
            out.append('%d DATA "%s"' % (n, r))
    print('\n'.join(out))
    print('%d faces, %d DATA lines; each face uses the same 16 characters' % (len(faces), len(out)),
          file=sys.stderr)

    if a.preview:
        S = 6
        W = 32 * S
        pad = 12
        sheet = Image.new('RGB', (len(faces) * (W + pad) + pad, W + 2 * pad), (0, 0, 0))
        for i, (caption, ink) in enumerate(faces):
            im = Image.new('RGB', (32, 32), PAL[a.paper])
            p = im.load()
            for y in range(32):
                for x in range(32):
                    if ink[y][x]:
                        p[x, y] = PAL[a.ink]
            sheet.paste(im.resize((W, W), Image.NEAREST), (pad + i * (W + pad), pad))
        sheet.save(a.preview)


if __name__ == '__main__':
    main()
