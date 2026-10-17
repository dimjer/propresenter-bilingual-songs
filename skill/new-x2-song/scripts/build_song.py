"""Build a new bilingual _x2 ProPresenter song file from a JSON spec.

Usage: python3 build_song.py spec.json out.pro

The document title is set to "<title>_x2"; name the file "<title>_x2.pro".

Spec:
{
  "title": "Example Song",
  "groups": [
    {"name": "Verse 1", "slides": [
      {"ua": ["рядок 1", "рядок 2"], "en": ["line 1", "line 2"]}
    ]},
    {"name": "Interlude", "slides": [{"ua": [], "en": []}]}
  ]
}

Layout per slide: 2+ UA lines -> theme "Песни X2", otherwise "Песни X1".
"""
import json
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbio import parse, serialize, get_path, set_path

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(HERE, 'templates')

# Paths inside a cue (see SKILL.md for the full map)
BASE = [(10, 0), (23, 0), (2, 0), (1, 0)]
EN, UA, RECT = 0, 1, 2
# Text element IDs shared by every slide of every song in the library
EN_ID = b'9DE13437-FDB8-443C-B474-ACB22889868A'
UA_ID = b'FB6EEB66-0613-4FE5-B272-E477248AB6DC'


def new_id():
    return str(uuid.uuid4()).upper().encode()


def uuid_msg(u):
    return serialize([(1, 2, u)])


def cues_of(path):
    return [r for f, w, r in parse(open(path, 'rb').read()) if f == 13]


def element(cue, layer):
    return get_path(cue, BASE + [(1, layer), (1, 0)])


def layout_of(cue):
    """Bounds of the 3 layers + the rectangle's element id."""
    return ([get_path(element(cue, L), [(3, 0)]) for L in (EN, UA, RECT)],
            get_path(element(cue, RECT), [(1, 0), (1, 0)]))


def rtf_header(rtf, ua):
    s = rtf.decode('utf-8')
    if ua:
        return s[:s.index('\\uc0') + len('\\uc0')]
    m = re.match(r'(.*?\\cb3 (?:\\outl0\\strokewidth-60 \\strokec3 )?)', s, re.S)
    return m.group(1)


def rtf_body(lines, ua):
    text = '\\\n'.join(lines)
    if ua:
        text = ''.join(ch if ord(ch) < 128 else '\\u%d ' % ord(ch) for ch in text)
    return text


def main(spec_path, out_path):
    spec = json.load(open(spec_path, encoding='utf-8'))
    tpl_bytes = open(os.path.join(TPL, 'x2_template.pro'), 'rb').read()
    tpl_top = parse(tpl_bytes)
    tpl_cue = [r for f, w, r in tpl_top if f == 13][0]
    tpl_group = [r for f, w, r in tpl_top if f == 12][0]
    colors = json.load(open(os.path.join(TPL, 'group_colors.json'), encoding='utf-8'))

    x2 = layout_of(tpl_cue)
    x1 = layout_of(cues_of(os.path.join(TPL, 'x1_reference.pro'))[0])
    hdr = {L: rtf_header(get_path(element(tpl_cue, L), [(13, 0), (5, 0)]), L == UA)
           for L in (EN, UA)}

    groups, cues, n = [], [], 0
    for gi, g in enumerate(spec['groups']):
        cue_ids = []
        for sl in g['slides']:
            n += 1
            ua, en = sl.get('ua', []), sl.get('en', [])
            bounds, rect_id = x2 if len(ua) >= 2 else x1
            c = tpl_cue
            cid = new_id()
            c = set_path(c, [(1, 0), (1, 0)], cid)
            c = set_path(c, [(2, 0)], (' %d' % n).encode())
            c = set_path(c, [(10, 0), (1, 0), (1, 0)], new_id())
            # unique per slide: ProPresenter caches thumbnails by this id
            c = set_path(c, BASE + [(7, 0), (1, 0)], new_id())
            for L, eid in ((EN, EN_ID), (UA, UA_ID), (RECT, rect_id)):
                p = BASE + [(1, L), (1, 0)]
                c = set_path(c, p + [(1, 0), (1, 0)], eid)
                c = set_path(c, p + [(3, 0)], bounds[L])
            for L, lines in ((EN, en), (UA, ua)):
                rtf = hdr[L] + rtf_body(lines, L == UA) + '}'
                c = set_path(c, BASE + [(1, L), (1, 0), (13, 0), (5, 0)], rtf.encode('utf-8'))
            cues.append(c)
            cue_ids.append(cid)

        h = get_path(tpl_group, [(1, 0)])
        h = set_path(h, [(1, 0), (1, 0)], new_id())
        h = set_path(h, [(2, 0)], g['name'].encode('utf-8'))
        if g['name'] in colors:
            h = set_path(h, [(3, 0)], bytes.fromhex(colors[g['name']]))
        h = set_path(h, [(5, 0), (1, 0)], new_id())
        groups.append(serialize([(1, 2, h)] + [(2, 2, uuid_msg(u)) for u in cue_ids]))

    top = []
    for f, w, r in tpl_top:
        if f == 2:
            r = uuid_msg(new_id())
        elif f == 3:
            r = (spec['title'] + '_x2').encode('utf-8')
        elif f in (12, 13):
            continue
        top.append((f, w, r))
        if f == 9:  # groups and cues go right after field 9, as in real files
            top += [(12, 2, g) for g in groups] + [(13, 2, c) for c in cues]
    out = serialize(top)
    assert serialize(parse(out)) == out
    open(out_path, 'wb').write(out)
    print('wrote %s: %d groups, %d slides' % (out_path, len(groups), len(cues)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
