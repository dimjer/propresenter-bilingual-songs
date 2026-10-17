"""Print groups, slides, layout (X1/X2) and decoded EN/UA text of an _x2 .pro file.

Usage: python3 inspect_song.py song.pro
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbio import parse, get_path

BASE = [(10, 0), (23, 0), (2, 0), (1, 0)]


def text(rtf):
    s = rtf.decode('utf-8', 'replace')
    if '{\\fonttbl}' in s:
        return []
    if '\\uc0' in s:
        body = s.split('\\uc0', 1)[1]
    else:
        m = re.search(r'\\cb3 (?:\\outl0\\strokewidth-60 \\strokec3 )?(.*)$', s, re.S)
        body = m.group(1) if m else ''
    body = re.sub(r'\}\s*$', '', body)
    body = re.sub(r'^(?:\\(?!u\d)[A-Za-z]+-?\d* ?\n?)+', '', body)
    body = re.sub(r'\\uc0', '', body)
    body = re.sub(r'\\u(\d+) ?', lambda m: chr(int(m.group(1))), body)
    return [l for l in body.split('\\\n')] if body.strip() else []


def label(c):
    return next((r.decode() for f, w, r in parse(c) if f == 2), '')


def main(path):
    top = parse(open(path, 'rb').read())
    print('title:', next(r for f, w, r in top if f == 3).decode())
    cues = {get_path(r, [(1, 0), (1, 0)]): r for f, w, r in top if f == 13}
    slide_ids = []
    for f, w, r in top:
        if f != 12:
            continue
        name = label(get_path(r, [(1, 0)])) or '(no name)'
        ids = [get_path(x[2], [(1, 0)]) for x in parse(r) if x[0] == 2]
        print('== %s (%d)' % (name, len(ids)))
        for u in ids:
            c = cues.get(u)
            if c is None:
                print('   MISSING cue', u)
                continue
            slide_ids.append(get_path(c, BASE + [(7, 0), (1, 0)]))
            bd = get_path(c, BASE + [(1, 2), (1, 0), (3, 0)])
            h = struct.unpack('<d', get_path(bd, [(2, 0), (2, 0)]))[0]
            lay = 'X2' if h > 250 else 'X1'
            el = lambda L: get_path(c, BASE + [(1, L), (1, 0), (13, 0), (5, 0)])
            print('  [%s]%s UA: %s' % (lay, label(c), ' / '.join(text(el(1)))))
            print('          EN: %s' % ' / '.join(text(el(0))))
    if len(set(slide_ids)) != len(slide_ids):
        print('!! WARNING: duplicate slide ids -> previews will all look the same')
    print('slides: %d, cues in file: %d' % (len(slide_ids), len(cues)))


if __name__ == '__main__':
    main(sys.argv[1])
