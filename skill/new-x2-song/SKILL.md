---
name: new-x2-song
description: Create a brand-new bilingual (Ukrainian + English) ProPresenter 7 song file ("<title>_x2.pro") from lyrics — use when the user asks to add/write/make a new song ("запиши пісню", "створи пісню", "запиши песню", "новая песня", "add a song"), or to inspect/check an _x2 .pro file's slides and text.
---

# New bilingual `_x2` song

Every song is a binary ProPresenter 7 `.pro` file named `<Title>_x2.pro`.
Each slide has a big **UA** text (primary, on a black bar) and a smaller **EN** text below it.
`scripts/build_song.py` builds such a file from a JSON spec by cloning a known-good slide
from `templates/`; never hand-edit protobuf.

Paths below are relative to this skill's folder. The target is the user's ProPresenter
library folder, usually
`~/Library/Application Support/RenewedVision/ProPresenter/UserWorkspaces/ProPresenter/Libraries/<Library name>/`.
If unsure which library, `ls` that `Libraries/` folder and ask the user.

## 1. Get the lyrics

- Use the lyrics the user gives (UA and EN). If EN is missing, ask whether to translate it
  yourself; mark self-made translations as such when reporting.
- Ask the user, don't guess, if section order or the slide split is unclear.

## 2. Split into slides

- **1 or 2 lines per slide**, UA and EN lines matching each other. Long lines → their own slide.
- Layout is chosen per slide: **2 UA lines → "X2" layout** (tall black bar),
  **1 UA line → "X1" layout** (short bar).
- Repeats ("Chorus x2") are **not** duplicated — each section is one group; the operator
  replays it live.
- Group names: use standard English names so colors are consistent:
  `Intro, Verse 1..4, PreChorus, Chorus, Chorus 1, Chorus 2, Bridge, Bridge 1..3,
  Interlude, Tag, Vamp, Ending, Outro` (colors in `templates/group_colors.json`).
- A slide with empty `ua` and `en` is an instrumental slide — it still shows the empty
  black bar. Ask the user before adding one.

## 3. Write the spec and build (in a temp/scratch folder)

```json
{
  "title": "Example Song",
  "groups": [
    {"name": "Verse 1", "slides": [
      {"ua": ["Перший рядок", "Другий рядок"], "en": ["First line", "Second line"]}
    ]},
    {"name": "Chorus", "slides": [
      {"ua": ["Один рядок"], "en": ["A single line"]}
    ]}
  ]
}
```

`title` is without `_x2` (the script stores `<title>_x2` as the document title).

```bash
python3 scripts/build_song.py <tmp>/spec.json "<tmp>/<title>_x2.pro"
python3 scripts/inspect_song.py "<tmp>/<title>_x2.pro"
```

Check the inspect output: every slide's UA/EN text is right, `[X1]`/`[X2]` matches the line
count, no `MISSING` or `duplicate slide ids` warning.

## 4. Install into the library

1. `pgrep -x ProPresenter` — if it prints anything, **stop and ask the user to close
   ProPresenter**. While open it watches the library folder and can overwrite/mutate files.
2. Don't overwrite an existing song without asking (`ls` the target name first).
3. Copy the file into the library folder, wait a few seconds, then run `inspect_song.py`
   on the installed copy to confirm it wasn't changed.
4. Tell the user to open ProPresenter and check the song.

## How the file works (for debugging)

- `scripts/pbio.py`: lossless protobuf wire parser. `parse(bytes) -> [(field, wiretype, raw)]`,
  `serialize`, `get_path/set_path(buf, [(field, occurrence), ...])`.
- Top level: `2` doc UUID, `3` title, `12` groups, `13` cues (slides); the rest is copied
  from the template.
- Group `12`: `{1: {1: uuid, 2: name, 3: color, 4: ?, 5: uuid}, 2*: cue uuid}`.
- Cue `13`: `1` cue uuid, `2` label `" N"`, `10/1` slide uuid,
  `10/23/2/1/7/1` **base-slide id — must be unique per slide** (ProPresenter caches the
  preview thumbnail by it; a shared id makes every preview show slide 1),
  `10/23/2/1/1[i]/1` layer i: 0 = EN text, 1 = UA text, 2 = black bar rectangle.
  In a layer element: `1/1` element id (EN/UA ids are shared by all slides; the bar id is the
  theme's X1 or X2 id), `3` bounds, `13/5` RTF.
- RTF: EN body is plain ASCII; UA body escapes every non-ASCII char as `\uNNNN ` (decimal,
  trailing space). Two lines are joined with a backslash + newline (`"\\\n"`).
- Layout geometry on a 1920×1080 canvas (Y / height): X1 — EN 859.6/97, UA 483.5/113,
  bar 439.3/201.4; X2 — EN 812.6/191, UA 428.5/223, bar 393.1/293.8.
- `templates/x2_template.pro` (slide template + X2 geometry) and `templates/x1_reference.pro`
  (X1 geometry) are one-slide placeholder files. To use your own look, replace them with a
  one-slide song designed in ProPresenter with the same 3 layers (EN text, UA text, bar).
