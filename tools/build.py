#!/usr/bin/env python3
"""Build disks/WOEILC.dsk from woeilc.bas using xdt99.

Usage: python3 tools/build.py [--xdt99 DIR] [--autorun]

  --xdt99 DIR   folder holding xbas99.py and xdm99.py (default: $XDT99_DIR,
                then ../xdt99)
  --keep-rem    keep comment text on the disk (default: strip it)
  --short       use the short program format (console memory only). The
                default is the long format, which needs the 32K expansion
                but has room for a much bigger program
  --autorun     also add a DSK1.LOAD program, so Extended BASIC runs the game
                as soon as it is selected

The script runs tools/content.py (content/game.txt) and tools/narration.py
(content/narration.txt) to refresh the DATA blocks, and
tools/check.py first, then tokenizes the program with
xbas99 (which also rejects bad syntax) and writes a 90 KB single-sided
disk image that js99er and Classic99 can both mount as DSK1.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'woeilc.bas')
OUT = os.path.join(ROOT, 'disks', 'WOEILC.dsk')
COMPILED_PACING = (225, 30, 130)  # TMAX, PD, SD in WOEILC-C


def run(cmd):
    print('+', ' '.join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xdt99', default=os.environ.get('XDT99_DIR') or os.path.join(ROOT, '..', 'xdt99'))
    ap.add_argument('--autorun', action='store_true')
    ap.add_argument('--keep-rem', action='store_true')
    ap.add_argument('--short', action='store_true')
    args = ap.parse_args()

    xbas = os.path.join(args.xdt99, 'xbas99.py')
    xdm = os.path.join(args.xdt99, 'xdm99.py')
    if not os.path.exists(xbas) or not os.path.exists(xdm):
        sys.exit('xdt99 not found in %s (use --xdt99 or set XDT99_DIR)' % args.xdt99)

    # content/game.txt is the source of the clue, location and loot data in woeilc.bas
    run([sys.executable, os.path.join(ROOT, 'tools', 'content.py'),
         os.path.join(ROOT, 'content', 'game.txt'), '--write', SRC])
    run([sys.executable, os.path.join(ROOT, 'tools', 'narration.py'),
         os.path.join(ROOT, 'content', 'narration.txt'), '--write', SRC])
    run([sys.executable, os.path.join(ROOT, 'tools', 'check.py'), SRC])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    with tempfile.TemporaryDirectory() as tmp:
        prog = os.path.join(tmp, 'WOEILC')
        src = SRC
        if not args.keep_rem:
            # Drop comment text but keep the lines: they are GOSUB/GOTO targets.
            src = os.path.join(tmp, 'woeilc_norem.bas')
            with open(SRC) as f, open(src, 'w') as g:
                for line in f:
                    num, _, rest = line.rstrip('\n').partition(' ')
                    g.write(num + ' REM\n' if rest.startswith('REM') else line)
        fmt = [] if args.short else ['-L']
        run([sys.executable, xbas, '-c'] + fmt + [src, '-o', prog])
        files = [prog]
        # WOEILC-C is the same program with the pacing values for the XB compiler (line 178),
        # because compiled code runs 30 or more times faster and the loops need real delays.
        comp_src = os.path.join(tmp, 'woeilc_c.bas')
        with open(src) as f:
            text = f.read()
        text, n = re.subn(r'(?m)^178 .*$', '178 TMAX=%d :: PD=%d :: SD=%d' % COMPILED_PACING, text)
        if n != 1:
            sys.exit('line 178 (TMAX, PD, SD) not found')
        with open(comp_src, 'w') as f:
            f.write(text)
        comp = os.path.join(tmp, 'WOEILC-C')
        run([sys.executable, xbas, '-c'] + fmt + [comp_src, '-o', comp])
        if args.autorun:
            load_src = os.path.join(tmp, 'load.bas')
            with open(load_src, 'w') as f:
                f.write('100 RUN "DSK1.WOEILC"\n')
            load = os.path.join(tmp, 'LOAD')
            run([sys.executable, xbas, '-c', load_src, '-o', load])
            files.append(load)
        # The long format is an INT/VAR 254 file; the short one is a PROGRAM file.
        fmt_arg = [] if args.short else ['-f', 'INTVAR254']
        run([sys.executable, xdm, OUT, '-X', 'sssd', '-a', prog] + fmt_arg + ['-n', 'WOEILC'])
        run([sys.executable, xdm, OUT, '-a', comp] + fmt_arg + ['-n', 'WOEILC-C'])
        if args.autorun:
            run([sys.executable, xdm, OUT, '-a', load])
    run([sys.executable, xdm, OUT, '-i'])
    run([sys.executable, xdm, OUT, '-C'])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
