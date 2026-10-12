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
line length limit, and plain ASCII. `xbas99` rejects bad syntax during the
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

* Start-up shows a three-page narration (lines 7100-7194) in the game's black,
  purple and yellow. Page 1 is on screen while the arrays and character shapes
  load, and the prompt appears once they are ready. Set 1 of the character
  colours holds `! " # $ % & '`, so those come out yellow on that screen.
* The tokenized program is about 12.4 KB, so it needs the 32K expansion (see the build notes).
* Witness portraits: draw a 32x32 PNG with ink and a transparent background, then run
  `python3 tools/face.py art/merchant.png`. It prints the `DATA` lines (colours, the unique 8x8
  blocks, and four row strings) that go after the quiz data at line 1400. `art/merchant.png` is
  witness 1. Lines 7400-7444 load the face during the narration and draw it on rows 4-7. All
  blocks of a face share one colour pair, and a face uses sets 9 and 10 (characters 96-111).
* The chase answer window is `TMAX` (line 178). One poll takes about 0.06 s
  at normal speed in js99er, so 120 is roughly 7 seconds.
* The travel map moves the plane with `CALL LOCATE` in 30 fixed steps, so it
  cannot overshoot or wrap. The first trip starts at the San Francisco office.
* Screen text uses columns 1-28 with `DISPLAY AT`, but `HCHAR` uses 1-32.
