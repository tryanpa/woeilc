#!/usr/bin/env python3
"""Compile content/narration.txt into the DATA block of woeilc.bas.

Usage: python3 tools/narration.py content/narration.txt            (print the DATA lines)
       python3 tools/narration.py content/narration.txt --write woeilc.bas

The block replaces BASIC lines 1500 to 1599. The title page starts at line 1500 and
the pages at 1510, 1530 and 1550, because the game does a RESTORE to each of them.
Each page is:  DATA <first screen row>,<number of rows>   then one DATA "text" per row.
Rows are already word wrapped and centred, so the game just prints them (routine 7340).
Quote marks are doubled (""), as Extended BASIC wants them, and the yellow rule is a row holding
just @, which the game draws with CALL HCHAR. The text has no escapes, so it can be typed into XB.
"""
import argparse
import re
import sys

FIRST, LAST = 1500, 1599
TITLE_LINE, PAGES_LINE = 1500, 1510
SLOT = 20                 # each page gets a slot of 20 lines: 1510, 1530, 1550
WIDTH = 28
MAX_ROWS_FROM = 17            # the viewport ends at row 17
RULE = 6


def wrap(text):
    """Break at the last space within 28 characters, like routine 8400 in the game."""
    out = []
    while len(text) > WIDTH:
        p = WIDTH
        while p > 1 and text[p - 1] != ' ':
            p -= 1
        if p <= 1:
            p = WIDTH
        out.append(text[:p].rstrip())
        text = text[p:]
    out.append(text)
    return out


def esc(s):
    return s.replace('"', '""')


def parse(path):
    pages = []
    cur = None
    errors = []
    for num, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n')
        if line.lstrip().startswith('#'):
            continue
        m = re.match(r'\[(title|page)(?:\s+start=(\d+))?\]\s*$', line.strip())
        if m:
            cur = {'kind': m.group(1), 'start': int(m.group(2) or 4), 'rows': [], 'line': num}
            pages.append(cur)
            continue
        if cur is None:
            if line.strip():
                errors.append('line %d: text before [title] or [page]' % num)
            continue
        if any(ord(c) > 126 for c in line):
            errors.append('line %d: plain ASCII only' % num)
            continue
        text = line.strip().upper()
        if not text:
            cur['rows'].append('')
        elif text == '---':
            cur['rows'].append('@')
        elif text.startswith('^'):
            for piece in wrap(text[1:].strip()):
                cur['rows'].append(' ' * ((WIDTH - len(piece)) // 2) + esc(piece))
        else:
            for piece in wrap(text):
                cur['rows'].append(esc(piece))
    # drop blank rows at the end of each page
    for pg in pages:
        while pg['rows'] and pg['rows'][-1] == '':
            pg['rows'].pop()
    if not pages or pages[0]['kind'] != 'title':
        errors.append('the first section must be [title]')
    if sum(1 for p in pages if p['kind'] == 'page') != 3:
        errors.append('the game shows exactly 3 [page] sections, found %d' %
                      sum(1 for p in pages if p['kind'] == 'page'))
    for pg in pages:
        last = pg['start'] + len(pg['rows']) - 1
        if last > MAX_ROWS_FROM:
            errors.append('the page at line %d runs to screen row %d (the limit is %d): shorten it' %
                          (pg['line'], last, MAX_ROWS_FROM))
    return pages, errors


def build(pages):
    out = []
    k = 0
    for pg in pages:
        if pg['kind'] == 'title':
            n, limit = TITLE_LINE, PAGES_LINE - TITLE_LINE
        else:
            n, limit = PAGES_LINE + SLOT * k, SLOT
            k += 1
        need = 1 + len(pg['rows'])
        if need > limit:
            sys.exit('a page at line %d needs %d DATA lines, the limit is %d' % (pg['line'], need, limit))
        out.append('%d DATA %d,%d' % (n, pg['start'], len(pg['rows'])))
        for r in pg['rows']:
            n += 1
            out.append('%d DATA "%s"' % (n, r))
    # pages are contiguous after the title block: renumber to avoid gaps
    for x in out:
        if len(x) > 140:
            sys.exit('generated line is too long: ' + x[:60])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('narration')
    ap.add_argument('--write', metavar='WOEILC.BAS')
    a = ap.parse_args()
    pages, errors = parse(a.narration)
    if errors:
        for e in errors:
            print('error:', e, file=sys.stderr)
        sys.exit(1)
    lines = build(pages)
    print('%d pages, %d DATA lines' % (len(pages), len(lines)), file=sys.stderr)
    if not a.write:
        print('\n'.join(lines))
        return
    src = [x for x in open(a.write).read().split('\n') if x.strip()]
    keep = [x for x in src if not FIRST <= int(x.split(' ', 1)[0]) <= LAST]
    allx = sorted(keep + lines, key=lambda x: int(x.split(' ', 1)[0]))
    new = '\n'.join(allx) + '\n'
    if new != open(a.write).read():
        open(a.write, 'w').write(new)
        print('updated', a.write, file=sys.stderr)
    else:
        print('unchanged', a.write, file=sys.stderr)


if __name__ == '__main__':
    main()
