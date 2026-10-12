#!/usr/bin/env python3
"""Offline checks for woeilc.bas. Standard library only.

Usage: python3 tools/check.py [path/to/woeilc.bas]

Checks:
  * no name is used both as an array and as a plain variable (XB rejects that
    at run time with IMPROPERLY USED NAME)
  * line numbers are present, unique and ascending
  * every GOTO, GOSUB, THEN, RESTORE and ON GOSUB target exists
  * lines fit XB's typing limit (5 screen lines of 28 columns)
  * the file is plain ASCII with no tabs
"""
import re
import sys

MAX_LEN = 140  # 5 screen lines of 28 characters
TARGET = re.compile(r'\b(?:GOSUB|GOTO|THEN|RESTORE)\s+(\d+)')
ON_GOSUB = re.compile(r'\bON\s+.+?\s+GOSUB\s+([\d,]+)')


# Words that look like names but are keywords, functions or subprograms.
RESERVED = set('''ABS ACCEPT AND AS AT ATN BASE BEEP CALL CHAR CHARPAT CHR$ CLEAR COINC COLOR COS DATA DELSPRITE DIGIT
DIM DISPLAY DISTANCE ELSE END EXP FOR GOSUB GOTO HCHAR IF INT KEY LEN LOCATE LOG MAGNIFY MOTION NEXT NOT NUMERIC
ON OPTION OR PATTERN POSITION POS RANDOMIZE READ REM RESTORE RETURN RND SCREEN SEG$ SGN SIN SIZE SOUND SPRITE SQR
STEP STOP STR$ TAN THEN TO VALIDATE VAL VCHAR ASC UALPHA'''.split())


def name_clashes(lines):
    scalar, array = {}, {}
    for n, text in lines.items():
        code = re.sub(r'"[^"]*"', '""', text)
        if re.match(r'\d+ (REM|DATA)', code):
            continue
        body = code.split(' ', 1)[1]
        for m in re.finditer(r"\b([A-Z][A-Z0-9]*\$?)(\()?", body):
            name, paren = m.group(1), m.group(2)
            if name in RESERVED or name.rstrip('$') in RESERVED:
                continue
            (array if paren else scalar).setdefault(name, n)
    return [(nm, array[nm], scalar[nm]) for nm in array if nm in scalar]


def check(path):
    problems = []
    lines = {}
    prev = -1
    with open(path, encoding='ascii', errors='replace') as f:
        raw = f.read().split('\n')
    for text in raw:
        if not text.strip():
            continue
        m = re.match(r'(\d+) ', text)
        if not m:
            problems.append('no line number: ' + text[:40])
            continue
        n = int(m.group(1))
        if n <= prev:
            problems.append('line %d is not ascending (after %d)' % (n, prev))
        prev = n
        lines[n] = text
        if len(text) > MAX_LEN:
            problems.append('line %d is %d chars (max %d)' % (n, len(text), MAX_LEN))
        if '\t' in text or any(ord(c) > 126 for c in text):
            problems.append('line %d has a tab or non-ASCII character' % n)
    for n, text in lines.items():
        # ignore REM text and quoted strings when looking for targets
        code = re.sub(r'"[^"]*"', '""', text)
        if re.match(r'\d+ REM', code):
            continue
        for m in TARGET.finditer(code):
            if int(m.group(1)) not in lines:
                problems.append('line %d jumps to missing line %s' % (n, m.group(1)))
        for m in ON_GOSUB.finditer(code):
            for t in m.group(1).split(','):
                if t and int(t) not in lines:
                    problems.append('line %d: ON GOSUB target %s is missing' % (n, t))
    for nm, a, b in name_clashes(lines):
        problems.append('%s is an array (line %d) and also a plain variable (line %d)' % (nm, a, b))
    return lines, problems


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'woeilc.bas'
    lines, problems = check(src)
    for p in problems:
        print('PROBLEM:', p)
    print('%d lines, %d problems' % (len(lines), len(problems)))
    sys.exit(1 if problems else 0)
