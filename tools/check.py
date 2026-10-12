#!/usr/bin/env python3
"""Offline checks for woeilc.bas. Standard library only.

Usage: python3 tools/check.py [path/to/woeilc.bas]

Checks:
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
    return lines, problems


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'woeilc.bas'
    lines, problems = check(src)
    for p in problems:
        print('PROBLEM:', p)
    print('%d lines, %d problems' % (len(lines), len(problems)))
    sys.exit(1 if problems else 0)
