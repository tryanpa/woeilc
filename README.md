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

* The chase answer window is `TMAX` (line 178). One poll takes about 0.06 s
  at normal speed in js99er, so 120 is roughly 7 seconds.
* The travel map moves the plane with `CALL LOCATE` in 30 fixed steps, so it
  cannot overshoot or wrap. The first trip starts at the San Francisco office.
* Screen text uses columns 1-28 with `DISPLAY AT`, but `HCHAR` uses 1-32.
