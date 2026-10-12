#!/usr/bin/env python3
"""Build disks/WOEILC.dsk from woeilc.bas using xdt99.

Usage: python3 tools/build.py [--xdt99 DIR] [--autorun]

  --xdt99 DIR   folder holding xbas99.py and xdm99.py (default: $XDT99_DIR,
                then ../xdt99)
  --keep-rem    keep comment text on the disk (default: strip it)
  --autorun     also add a DSK1.LOAD program, so Extended BASIC runs the game
                as soon as it is selected

The script runs tools/check.py first, then tokenizes the program with
xbas99 (which also rejects bad syntax) and writes a 90 KB single-sided
disk image that js99er and Classic99 can both mount as DSK1.
"""
import argparse
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'woeilc.bas')
OUT = os.path.join(ROOT, 'disks', 'WOEILC.dsk')


def run(cmd):
    print('+', ' '.join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xdt99', default=os.environ.get('XDT99_DIR') or os.path.join(ROOT, '..', 'xdt99'))
    ap.add_argument('--autorun', action='store_true')
    ap.add_argument('--keep-rem', action='store_true')
    args = ap.parse_args()

    xbas = os.path.join(args.xdt99, 'xbas99.py')
    xdm = os.path.join(args.xdt99, 'xdm99.py')
    if not os.path.exists(xbas) or not os.path.exists(xdm):
        sys.exit('xdt99 not found in %s (use --xdt99 or set XDT99_DIR)' % args.xdt99)

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
        run([sys.executable, xbas, '-c', src, '-o', prog])
        files = [prog]
        if args.autorun:
            load_src = os.path.join(tmp, 'load.bas')
            with open(load_src, 'w') as f:
                f.write('100 RUN "DSK1.WOEILC"\n')
            load = os.path.join(tmp, 'LOAD')
            run([sys.executable, xbas, '-c', load_src, '-o', load])
            files.append(load)
        run([sys.executable, xdm, OUT, '-X', 'sssd', '-a'] + files + ['-n', 'WOEILC'])
    run([sys.executable, xdm, OUT, '-i'])
    run([sys.executable, xdm, OUT, '-C'])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
