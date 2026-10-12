#!/usr/bin/env python3
"""Compile content/game.txt into the DATA block of woeilc.bas.

Usage: python3 tools/content.py content/game.txt            (print the DATA lines)
       python3 tools/content.py content/game.txt --write woeilc.bas

The block replaces BASIC lines 1000 to 1199:
  1011 DATA <locations>,<loot items>
  loot items (from 1012):  DATA "ITEM","DESCRIPTION"
  locations (from 1100):   DATA "NAME",<number of clues>   then one DATA "CLUE" line per clue
The game reads this once at start-up, in two chunks (RESTORE 1011 and RESTORE 1100).

Checks: lengths, characters, a spoiler warning when a clue contains a word of its
own location's name, and the number of screen lines each clue takes, using the same
word wrap as the game (routine 8400).
"""
import argparse
import re
import sys

FIRST, LAST = 1000, 1199
LOC_LINE = 1100          # the game does RESTORE 1100 to read the locations
MAX_NAME, MAX_CLUE, MAX_ITEM, MAX_DESC = 24, 108, 40, 56
MAX_CLUE_LINES = 5
STOP = {'USA', 'UK', 'UNIV', 'UNIVERSITY', 'PARK', 'LABS', 'OF', 'THE', 'MENLO'}


def wrap_lines(text, width=28):
    """Count lines the way routine 8400 breaks them: at the last space within 28."""
    n = 0
    while len(text) > width:
        p = width
        while p > 1 and text[p - 1] != ' ':
            p -= 1
        if p <= 1:
            p = width
        text = text[p:]
        n += 1
    return n + 1


def parse(path):
    loot, locs = [], []
    cur = None
    section = None
    errors, warns = [], []
    for num, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.split('#', 1)[0].strip() if not raw.lstrip().startswith('#') else ''
        if not line:
            continue
        if line.lower() == '[loot]':
            section = 'loot'
            continue
        if line.lower() == '[location]':
            section = 'loc'
            cur = {'name': None, 'clues': [], 'line': num}
            locs.append(cur)
            continue
        if any(ord(c) > 126 for c in line) or '"' in line:
            errors.append('line %d: only plain ASCII and no double quote marks' % num)
            continue
        if section == 'loot':
            item, _, desc = [p.strip() for p in line.partition('|')]
            loot.append((item.upper(), desc.upper(), num))
        elif section == 'loc':
            key, _, val = [p.strip() for p in line.partition('=')]
            if key.lower() == 'name':
                cur['name'] = val.upper()
            elif key.lower() == 'clue':
                cur['clues'].append((val.upper(), num))
            else:
                errors.append('line %d: expected name = or clue =' % num)
        else:
            errors.append('line %d: text before [loot] or [location]' % num)

    if not 1 <= len(loot) <= 12:
        errors.append('need 1 to 12 loot items, found %d' % len(loot))
    if not 6 <= len(locs) <= 12:
        errors.append('need 6 to 12 locations, found %d' % len(locs))
    for item, desc, num in loot:
        if not item or not desc:
            errors.append('line %d: loot needs "item | description"' % num)
        if len(item) > MAX_ITEM:
            errors.append('line %d: item is %d characters (max %d)' % (num, len(item), MAX_ITEM))
        if len(desc) > MAX_DESC:
            errors.append('line %d: description is %d characters (max %d)' % (num, len(desc), MAX_DESC))
    for loc in locs:
        nm = loc['name']
        if not nm:
            errors.append('line %d: location has no name' % loc['line'])
            continue
        if len(nm) > MAX_NAME:
            errors.append('%s: name is %d characters (max %d)' % (nm, len(nm), MAX_NAME))
        if not 1 <= len(loc['clues']) <= 5:
            errors.append('%s: needs 1 to 5 clues, found %d' % (nm, len(loc['clues'])))
        words = [w for w in re.findall(r"[A-Z0-9]+", nm) if w not in STOP and len(w) >= 3]
        for clue, num in loc['clues']:
            if len(clue) > MAX_CLUE:
                errors.append('line %d: clue is %d characters (max %d)' % (num, len(clue), MAX_CLUE))
            if wrap_lines(clue) > MAX_CLUE_LINES:
                errors.append('line %d: clue wraps to %d screen lines (max %d)' % (num, wrap_lines(clue), MAX_CLUE_LINES))
            for w in words:
                if re.search(r'\b%s\b' % re.escape(w), clue):
                    warns.append('line %d: the clue for %s contains "%s", which gives the place away' % (num, nm, w))
    return loot, locs, errors, warns


def build(loot, locs):
    out = ['%d REM === GENERATED FROM content/game.txt BY tools/content.py: EDIT THAT FILE ===' % FIRST]
    n = 1011
    out.append('%d DATA %d,%d' % (n, len(locs), len(loot)))
    for item, desc, _ in loot:
        n += 1
        out.append('%d DATA "%s","%s"' % (n, item, desc))
    if n >= LOC_LINE:
        sys.exit('the loot block needs lines up to %d, it must end before %d' % (n, LOC_LINE))
    n = LOC_LINE - 1
    for loc in locs:
        n += 1
        out.append('%d DATA "%s",%d' % (n, loc['name'], len(loc['clues'])))
        for clue, _ in loc['clues']:
            n += 1
            out.append('%d DATA "%s"' % (n, clue))
    if n >= LAST:
        sys.exit('content needs lines up to %d, the limit is %d' % (n, LAST - 1))
    for x in out:
        if len(x) > 140:
            sys.exit('generated line is too long (%d): %s' % (len(x), x[:60]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('content')
    ap.add_argument('--write', metavar='WOEILC.BAS')
    a = ap.parse_args()

    loot, locs, errors, warns = parse(a.content)
    for w in warns:
        print('warning:', w, file=sys.stderr)
    if errors:
        for e in errors:
            print('error:', e, file=sys.stderr)
        sys.exit(1)
    lines = build(loot, locs)
    clues = sum(len(l['clues']) for l in locs)
    chars = sum(len(c) for l in locs for c, _ in l['clues'])
    print('%d locations, %d clues (%d characters), %d loot items, %d DATA lines' %
          (len(locs), clues, chars, len(loot), len(lines)), file=sys.stderr)

    if not a.write:
        print('\n'.join(lines))
        return
    src = [x for x in open(a.write).read().split('\n') if x.strip()]
    keep = [x for x in src if not FIRST <= int(x.split(' ', 1)[0]) <= LAST]
    allx = keep + lines
    allx.sort(key=lambda x: int(x.split(' ', 1)[0]))
    new = '\n'.join(allx) + '\n'
    old = open(a.write).read()
    if new != old:
        open(a.write, 'w').write(new)
        print('updated', a.write, file=sys.stderr)
    else:
        print('unchanged', a.write, file=sys.stderr)


if __name__ == '__main__':
    main()
