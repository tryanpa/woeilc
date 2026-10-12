# woeilc
Where on Earth is Lucia Cupertino

A computing history chase for the TI-99/4A, written in Extended BASIC.
`woeilc.bas` is the source, kept as plain text so it diffs cleanly.

## Try it in js99er or Classic99

A ready-made disk image is in `disks/WOEILC.dsk` (90 KB, single sided).

1. Start Extended BASIC.
2. Mount `disks/WOEILC.dsk` as DSK1 (the Load disk button in js99er).
3. Type `OLD DSK1.WOEILC`, wait for the prompt to come back, then `RUN`.

At normal speed the load and the start-up scan take a while, and keys
pressed during disk access are dropped. Wait for the prompt before typing.

## Working on the code

Edit `woeilc.bas`, then:

```
python3 tools/check.py     # offline lint, no emulator needed
python3 tools/build.py     # lint, tokenize, write disks/WOEILC.dsk
```

`build.py` needs [xdt99](https://github.com/endlos99/xdt99). Point it at a
checkout with `--xdt99 DIR` or the `XDT99_DIR` variable (default `../xdt99`).
The disk copy has comment text stripped (about 12% smaller; a shorter start-up scan is likely but not
measured); `--keep-rem` leaves it in. `--autorun` also adds a `DSK1.LOAD`
file so XB starts the game by itself.

The program is stored in the long format by default (an `INT/VAR 254` file), which needs the
32K memory expansion but has room for a much larger program. The short format keeps the program
in console video memory and stopped working at about 12 KB: `RUN` returned straight to `READY`
with no message. `--short` still builds it, for a program that is small enough.

`check.py` verifies line numbers, that every jump target exists, XB's
line length limit, plain ASCII, and that no name is used as both an array and a plain
variable (XB stops with IMPROPERLY USED NAME). `xbas99` rejects bad syntax during the
build, so a disk is only produced from a program that tokenizes.

Anything about timing, sprites, screen layout and sound still needs a run in
the emulator. The scenarios worth stepping through after a change are a win,
a wrong arrest, "too slow" in the chase, running out of turns, play again,
and quit.

## What things cost (js99er at normal speed)

Measured with small benchmark programs. Real hardware should be close.

| Operation | Time |
|---|---|
| one BASIC statement | about 10 ms |
| one `FOR`/`NEXT` iteration | 6 ms |
| `CALL HCHAR` | 32 ms plus 1.1 ms per character |
| `DISPLAY AT` | 30 ms plus about 1.2 ms per character |
| `CALL CLEAR`, `CALL COLOR` | about 25 ms |
| `CALL CHAR` | 89 ms |
| `READ` | 35 to 43 ms |
| `RESTORE` | 125 ms near the top of the program, 215 ms further down |

`RESTORE` has to scan for its line, so it gets slower the deeper the target
is. That is why all the `DATA` is read once at start-up into arrays and the
game never calls `RESTORE` again. Clearing the viewport only covers the rows
the last screen used, the status line is redrawn only when the turns change,
and `ACCEPT ... VALIDATE(DIGIT)` replaces the old digit-checking loop.

## Notes

* Start-up shows a title page and three narration pages, in the game's black, purple and yellow,
  inside a yellow frame. The text is in `content/narration.txt`; `tools/narration.py` word wraps
  and centres it into lines 1500 to 1599 (the build runs it). The game's data load (about 5 s)
  starts as soon as the title page is drawn, and the PRESS ANY KEY prompt appears when it is done.
  Set 1 of the character colours holds `! " # $ % & '`, so those come out yellow on those screens.
* Memory. With the 32K expansion, Extended BASIC `SIZE` reports 11,840 bytes of stack (variables and
  strings) and 24,488 bytes of program space before the game loads. While the game runs, about 3,500
  bytes of stack and 4,600 bytes of program space are left. The stack is the tight one: every clue,
  caption and quiz string lives there, and when it fills, BASIC pauses for a few seconds to garbage
  collect. Adding locations or clues grows it, so read content lazily or trim it if pauses appear.
* Data line map: title 1500, narration pages 1510, 1530 and 1550, loot 1011, locations from 1100,
  herrings 1201, quiz 1301, faces 1400. The loader is split into chunks (7051 to 7059) that run
  between the narration pages, so the load hides behind the story.
* The tokenized program is about 19.2 KB, so it needs the 32K expansion (see the build notes).
* Game content lives in `content/game.txt`: the loot items and the pool of locations with their
  clues. `tools/content.py` checks it (lengths, plain ASCII, a warning when a clue names its own
  place, and how many screen lines each clue takes) and writes it into lines 1000 to 1199 of
  `woeilc.bas`; `tools/build.py` runs it for you. Edit the text file, never those lines. A game
  uses `RL` (6) locations from a shuffled bag of all `NL`, so successive games cycle through every
  location before any repeats. The loot is picked at random, never the same twice in a row, and
  only changes the story text. Each witness gives one of the location's clues at random, not the
  one given last time. Every game still opens with the first lead.
* The cast of witnesses is listed in `art/cast.txt` (a 32x32 PNG and a caption per line). Run
  `python3 tools/face.py art/cast.txt` to get the `DATA` lines that replace the block at line 1400.
  Draw each face as black ink on a transparent background. The cast needs 3 to 12 faces.
  At each stop, `7500` deals three different faces from the shuffled cast to the three witnesses,
  and the roster shows their captions.
* Character slots. Only characters 96 to 143 can be given colours: `CALL COLOR` rejects colour sets
  15 and 16 (characters 144 to 159) with BAD VALUE, so those cannot be used for coloured graphics.
  Characters 136 to 143 are used by the game, and sprites draw from the same patterns as
  characters, so they save nothing. Graphics share fixed slots instead of owning characters:

  | Slot | Characters | Colour sets | Use |
  |---|---|---|---|
  | face | 96-111 | 9, 10 | the witness portrait, 16 characters |
  | free | 112-127 | 11, 12 | a 16-character picture slot, such as a location picture |
  | frame | 128-132 | 13 | the yellow frame of the title and narration; free again once the intro ends |
  | spare | 133-135, 137 | 13, 14 | four characters |

  Every face reuses the face slot, so a bigger cast costs no extra characters, only a little data.
  A face is four row strings; each row is loaded with one `CALL CHAR` and drawn as soon as it is
  ready, so the face appears row by row after the text. `CURF` remembers which face is loaded, so
  asking the same witness again reloads nothing. A swap costs about 1.3 s, because `CALL CHAR` takes
  about 90 ms per character and batching four per call barely helps. To add a new kind of graphic,
  give it its own slot in the free range, load it with the same row-at-a-time pattern, and track
  what is loaded so it can be skipped.
* The chase answer window is `TMAX` (line 178). One poll takes about 0.06 s
  at normal speed in js99er, so 120 is roughly 7 seconds.
* The travel map moves the plane with `CALL LOCATE` in 30 fixed steps, so it
  cannot overshoot or wrap. The first trip starts at the San Francisco office.
* Screen text uses columns 1-28 with `DISPLAY AT`, but `HCHAR` uses 1-32.
