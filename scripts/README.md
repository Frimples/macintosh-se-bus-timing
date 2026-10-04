# Scripts

Tools that produced every measurement in this repository. Deterministic, and
runnable with **Python 3 and NumPy only** — no sigrok installation required.

## Quick start

```
bash scripts/reproduce.sh
```

That reads the shipped `.sr` captures, produces every published floppy and clock
number, and prints the expected values at the end.

## Files

| Script | Purpose |
|---|---|
| `sr_to_arrays.py` | Read a sigrok `.sr` capture into per-channel transition arrays |
| `vcd_to_arrays.py` | Same, from a VCD export. Alternative input path |
| `clock_c16m.py` | Measure C16M three independent ways; fails if they disagree |
| `floppy_rw_discriminator.py` | The primary result: the `/LDS` read/write discriminator |
| `export_summaries.py` | Generate the CSV files in `data/stock/` |
| `reproduce.sh` | End-to-end: captures to published numbers |

## Why there is a direct `.sr` reader

The obvious route is `sigrok-cli -I sigrok -O vcd`. **This was attempted and
fails** on the reference host: the installed sigrok-cli (0.6.0-git-0bc24877)
builds without the srzip input module, so `-I sigrok` reports
`Input module 'sigrok' not found`.

`sr_to_arrays.py` therefore reads the container directly.

### Container layout

A sigrok `.sr` file is a ZIP archive:

| Member | Contents |
|---|---|
| `version` | 1 byte |
| `metadata` | `KEY=VALUE` lines, including `total probes=N` and `probeK=NAME` |
| `logic-1-N` | concatenated fixed-width sample rows |

With 16 channels a sample row is **2 bytes**, so 2 bytes per sample. Bits are
packed **LSB-first within each byte**, and probe order follows the `probeK=NAME`
lines: probe1 is bit 0 of byte 0, probe2 bit 1 of byte 0, ... probe8 bit 7 of
byte 0, probe9 bit 0 of byte 1, and so on.

### This layout was validated, not assumed

Because the layout was determined empirically, it was checked directly: one
capture was decoded both ways — natively from `.sr`, and via the VCD path
already used for the original analysis — and **all 16 per-channel transition
counts were compared. All 16 matched exactly.**

That is a strong check. It validates the bit-packing order and channel
ordering, not merely the sample count. See `docs/methodology.md` §6.

## Requirements

- Python 3.8 or later
- NumPy

```
python3 -c "import numpy; print(numpy.__version__)"
```

Verified against Python 3.13 and NumPy 2.x. No other dependency.

## Invocation

```
# stage 1: capture -> transition arrays
python3 scripts/sr_to_arrays.py CAPTURE.sr OUTDIR \
        --timescale-ns 10 --rename PMCYC=DACK

# stage 2: clock, three methods, refuses to report if they disagree
python3 scripts/clock_c16m.py OUTDIR

# stage 3: the primary discriminator, non-zero exit if not clean
python3 scripts/floppy_rw_discriminator.py READ_DIR WRITE_DIR

# stage 4: CSV summaries
python3 scripts/export_summaries.py WORK_DIR
```

## Expected input

`CAPTURE.sr` — an unmodified sigrok capture from `captures/stock/`.

`OUTDIR` receives `tr.npz` (arrays `ts_<NAME>` and `vs_<NAME>`) and
`parse_report.txt`.

## Expected output

| Script | Key output |
|---|---|
| `clock_c16m.py` | `15.6671 MHz`, period `63.8281 ns`, all three methods agreeing |
| `floppy_rw_discriminator.py` | `91500` read cycles, `717` write cycles, separation `100%, ZERO OVERLAP` |
| `export_summaries.py` | three CSVs in `data/stock/` |

Both analysis scripts **exit non-zero** when their check fails, so a broken
probe setup cannot silently produce a clean-looking result.

## Assumptions

**1. VCD timescale is 10 ns.** Every capture here is 100 MHz, one sample per
10 ns, so timestamps are in 10 ns units and the scripts multiply by 10 to get
nanoseconds. This is stated rather than read from the file. `sr_to_arrays.py`
reports the samplerate from metadata but does not enforce a timescale; pass
`--timescale-ns` explicitly if a capture ever differs.

**2. Active-low signals.** `/AS`, `/DTACK`, `/UDS` and `/LDS` are active-low:
logic 0 means active. **This is not inferred from signal names** — sigrok strips
the leading slash, so a header on `/LDS` reads `LDS` with no negation marker,
and inferring polarity from that produced a false conflict twice before it was
caught.

Polarity was established from documented SE bus behaviour and then corroborated
against the data: `/DTACK` is observed releasing 100-110 ns **after** `/AS`
rises on every acknowledged cycle, never before. That ordering only holds if
both are read active-low. The scripts therefore report `0 = ACTIVE`, and every
"active at `/AS`" statement means "low at `/AS`".

`DACK` (channel 7) is a separate acknowledge line, not covered by this.

**3. Probe order follows metadata.** Channel identities come from the
`probeK=NAME` lines in the capture's own metadata — not from a hard-coded
order. This is what makes the rename mechanism below possible.

## Channel-metadata corrections WITHOUT modifying raw captures

Several captures embed a label that is known to be wrong: they say `PMCYC` for
CH7, which was physically clipped to **DACK**. **PMCYC was never captured.**

**Originals are never edited.** They are shipped exactly as acquired, wrong
label included — that label is evidence of what the acquisition software was
told, and editing it would destroy the record.

The correction is applied when data is loaded:

```
python3 scripts/sr_to_arrays.py CAPTURE.sr OUTDIR --rename PMCYC=DACK
```

`reproduce.sh` does this for both floppy captures. `export_summaries.py` and
`floppy_rw_discriminator.py` then consume the corrected arrays.

`parse_report.txt` records the rename that was applied, so it is always visible
which name a given array came from.

Note that the primary result — the `/LDS` discriminator — does not depend on CH7
at all. It reads `/AS`, `/LDS`, `/UDS`, `/R/W` and the address lines.

## Notes on the shipped scripts

These derive from the original private analysis scripts, which were **not
modified**. Corrections were applied to the copies:

| Corrected in the published copy | Detail |
|---|---|
| VCD timestamp/value-change on one line | `#0 0! 1"` — the original dropped every value change on such lines and returned **zero transitions on all 16 channels** |
| VCD symbol lookup | was keyed incorrectly, mis-naming channels |
| C16M half-period | the original measured consecutive *transitions* and reported 31.3342 MHz — twice the true frequency |
| CH7 interpretation | was PMCYC; physically DACK |
| A23:A19 mask | was `(0,1,0,1,1)`; inverted, and returned zero floppy cycles |
| Private paths | all paths are now relative |

Each is recorded in `docs/corrections-and-errata.md`.

## Adding a script

Read `CONTRIBUTING.md` first. In particular: make it fail loudly on bad input,
guard the address bit order, and never edit a capture.
