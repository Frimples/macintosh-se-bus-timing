# Stock bus baseline

Shared timing baseline common to all workloads. Figures are OBSERVED MEASUREMENT,
re-derived from the shipped captures.

## Processor clock

**C16M = 15.6671 MHz. Period = 63.83 ns.**

Measured three independent ways, agreeing to within 0.00001 MHz on all three
captures:

| Method | Result |
|---|---|
| rising-to-rising | 63.8279-63.8281 ns -> 15.6671 MHz |
| falling-to-falling | 63.8279-63.8281 ns -> 15.6671 MHz |
| transitions / 2 / duration | 15.6671 MHz |

**DOCUMENTED EXTERNAL FACT.** Apple, *Guide to the Macintosh Family Hardware*,
2nd ed., Appendix A: C16M = 15.6672 MHz. Measured value deviates by 0.001%.

At 8 MHz CPU with a 15.6671 MHz bus clock, the ratio is consistent with the
documented 2:1 clocking.

**Clock period dithers between 60 ns and 70 ns** in the raw histogram. This is
expected — 63.83 ns does not divide evenly into the 10 ns sample grid — and is
not instability. The mean over many edges recovers the true period.

**Do not compute a frequency from the edge-to-edge interval.** That is the
half-period and gives 31.914 ns. Reporting it as a frequency was an analysis
error, corrected and documented in `docs/corrections-and-errata.md`.

## Bus cycle timing

### `/AS` to `/DTACK` (T1)

| Capture | 90 ns | 100 ns | 110 ns | Other |
|---|---|---|---|---|
| floppy-read (all cycles) | 143,719 | 549,565 | 11 | sparse 220-1000 ns tails |
| post-fall sanity (20 ms) | 3,293 | 24,571 | 25 | 350/360/600/610/860/870 |
| SCSI region | FAST 90-100 ns | | | LONG 1110-1130 ns |

The dominant floppy values are **90 and 100 ns**. Higher values (350, 600, 860)
appear sparsely on all-cycle populations and correspond to asynchronous
peripheral waits, not floppy traffic.

**There is no long-acknowledge class on floppy.** The SCSI LONG population has
no counterpart in floppy traffic at all.

### `/AS` cycle duration

310 ns and 320 ns dominate. Both are clock-quantised multiples of the 63.83 ns
C16M period.

### `/DTACK` retirement

**`/DTACK` releases 100-110 ns after `/AS` rises. Never before.**

| Capture | 100 ns | 110 ns | Negative |
|---|---|---|---|
| floppy-read | 482,611 | 252,848 | **0** |
| floppy-write | 506,067 | 269,417 | **0** |

This is correct 68000 bus discipline and it is **identical for reads and
writes**. It is therefore *not* a read/write discriminator — but it is the
single best test of whether a substituted CPU reproduces stock bus timing, since
a CPU driving `/DTACK` release on the wrong edge would show up here immediately
as a negative or near-zero delay.

### Acknowledgement coverage

| Capture | Complete `/AS` cycles | Unacknowledged | Orphan `/DTACK` |
|---|---|---|---|
| floppy-read | 756,949 | 14,239 | **0** |
| floppy-write | 789,725 | — | — |
| SCSI region | 39,503 | **0** | **0** |
| post-fall sanity | 30,089 | 4 (0.01%) | **0** |

Zero orphan `/DTACK` on every capture: `/DTACK` is never asserted outside an
`/AS` cycle. That is a direct check that the acknowledge line is behaving.

The unacknowledged fraction varies with workload — roughly 10-12% on floppy
captures, near zero on SCSI — because it reflects how many cycles the CPU issues
without waiting on a peripheral. It is a workload property, not a bus fault.

## Address and control setup

| Signal | Setup relative to `/AS` |
|---|---|
| A3, A4, A5 | **-50 ns dominant**, -60 ns second |
| R/W (write cycles) | **-10 ns** — settles at the `/AS` edge |
| R/W (read cycles) | stable well before `/AS` |

Textbook 68000 setup behaviour, consistent across every capture. **Zero in-cycle
address transitions** on acknowledged cycles — the address bus is stable for the
whole transaction.

This doubles as a positive check that the address probes are sound: a mis-seated
probe would not produce clean -50 ns setup.

## Data strobes

`/UDS` and `/LDS` assert within every bus cycle, typically twice per cycle
(assert then release). Over a full capture they are asserted roughly half the
time and deasserted roughly half the time, with each strobe asserting alone only
occasionally.

**Workload-specific asymmetry** — see `docs/stock-floppy-read-write.md`. On
floppy reads `/LDS` is active at `/AS` while `/UDS` is inactive; on floppy writes
neither strobe is active at the `/AS` edge and `/LDS` asserts ~125 ns later. This
is the primary published discriminator.

## Static signals

| Signal | Behaviour |
|---|---|
| DRQ (AM5380 pin 22) | **static high** on every non-SCSI capture and on the post-fall capture |
| DACK (SCSI DMA acknowledge) | **static high** across 500 ms of floppy read *and* 500 ms of floppy write |

Both are correct readings, not faults. The 5380 is idle during floppy activity.
On stock hardware, DACK never asserts during normal programmed-I/O floppy
traffic while `/DTACK` acknowledges every cycle — a **negative reference
observation**, valuable as a stock comparator and nothing more. It is **not**
evidence about pseudo-DMA use in general. See `docs/probe-map.md`.

## Address space observed

Decoded from A23:A19 on the post-fall sanity capture, where the machine was
running ordinary code:

| A23:A19 | Address range | Meaning | Share |
|---|---|---|---|
| 01000 | `$400000-$43FFFF` | ROM — code executing | 56.84% |
| 00000 | `$000000-$07FFFF` | RAM (post-boot placement) | 28.23% |
| 00111 | `$380000-$3FFFFF` | RAM | 14.92% |
| 11011 | `$D80000-$DBFFFF` | IWM floppy | **absent** (no floppy activity) |
| 01011 | `$580000-$5FFFF` | SCSI device select | **absent** (5380 idle) |

The absence of the floppy and SCSI regions in this capture is expected — it was
an idle/post-fall sanity capture, not a peripheral workload — and it is why DRQ
and DACK could not be validated by activity in that capture.

The ROM/RAM split confirms **A22, A21, A20 and A19 are working correctly and
collectively**.

## Quantisation caveat

Every figure is quantised to **10 ns**. Two measurements differing by less than
10 ns cannot be distinguished, and where a distribution shows two adjacent values
(90/100 ns, or +120/+130 ns) those are usually one physical edge quantised either
side of a sample boundary.

Nothing in this dataset depends on resolving finer than 10 ns.
