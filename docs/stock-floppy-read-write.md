# Stock floppy read vs write baseline

This is the **primary result** of this dataset.

All figures below are OBSERVED MEASUREMENT, re-derived from the shipped
`.sr` captures. Reproduce with:

```
bash scripts/reproduce.sh
```

## The discriminator

On a stock Macintosh SE, the `/LDS` data strobe is **active at `/AS`
assertion for a floppy read** and **inactive at `/AS` assertion for a floppy
write**, asserting 120-130 ns later.

| | `/LDS` at `/AS` | first `/LDS` assertion |
|---|---|---|
| **READ** | ACTIVE on 91,500 of 91,500 (100%) | offset 0 ns, or already active |
| **WRITE** | ACTIVE on 0 of 717 (0%) | +120 ns (348) / +130 ns (369) |

**Separation is 100% with zero overlap**, over 91,500 read cycles and 717 write
cycles.

This is the useful property: it is **decode-independent**. It requires no
register identification, no address-bit interpretation, and no assumption about
which controller register is being touched. It can be measured on any capture
where the floppy bus is active.

`scripts/floppy_rw_discriminator.py` exits non-zero if the separation is not
clean, so a failing probe setup cannot silently produce a clean-looking result.

### Note on the +120/+130 ns split

Those are not two distinct events. Both are the same physical edge falling either
side of a 10 ns sample boundary — see `docs/methodology.md` §3. Treat it as one
event at approximately +125 ns.

## Read this before interpreting the write capture

**The "floppy write" capture is 98.85% reads.**

| | Count | Share of floppy population |
|---|---|---|
| Reads (R/W = 1) | 61,716 | 98.85% |
| Writes (R/W = 0) | **717** | 1.15% |

Anyone reading from the filename alone would reasonably expect mostly writes.
That would be wrong. This is consistent with the IWM write protocol, where the
byte to be written is staged by reading current contents first, but it means:

- **717 write cycles** is enough to establish the `/LDS` phase signature — it
  is 100% clean.
- **717 write cycles is not** enough to characterise write-cycle timing
  distributions the way 91,500 read cycles allow. The write-cycle timing figures
  below should be read with that in mind.

## Populations

| Capture | Complete `/AS` cycles | Floppy-window cycles | Reads | Writes |
|---|---|---|---|---|
| floppy-read | 756,949 | **91,500** | 91,500 | 0 |
| floppy-write | 789,725 | **62,433** | 61,716 | 717 |

Floppy window identified by **A23:A19 = 11011** at `/AS`, the top-2 MB decode
window containing the IWM floppy controller.

> **Bit-order trap.** A23:A19 = 11011 means A23=1, A22=1, A21=0, A20=1, A19=1.
> Writing the mask as (0,1,0,1,1) returns **zero** floppy cycles while every
> individual term is non-zero — it silently selects the ROM window instead. The
> published scripts assert that the ROM window is also present, so this inversion
> fails loudly rather than quietly.

## Timing

### `/AS` to `/DTACK` (T1)

| Population | 90 ns | 100 ns | 110 ns |
|---|---|---|---|
| READ (91,500) | 11,516 | 79,984 | — |
| WRITE-capture reads (61,716) | 7,081 | 54,635 | — |
| WRITE-capture writes (717) | 10 | 697 | **10** |

Reads and writes share the same two dominant values. Writes add a small 110 ns
population (10 of 717, 1.39%).

**There is no long-acknowledge class on floppy.** The 1110-1130 ns population
seen on SCSI does not appear here at all. Any assumption that the SCSI long
class is a general synchronous-peripheral signature is contradicted by this
data.

### `/AS` cycle duration

310 ns and 320 ns dominate in both captures (310: 44,134 / 320: 47,366 on reads;
310: 267 / 320: 450 on writes). Clock-quantised, as expected.

### `/DTACK` retirement — identical for reads and writes

`/DTACK` releases **100-110 ns after `/AS` rises** on every acknowledged cycle,
never before.

- READ: 100 ns on 482,611; 110 ns on 252,848. Negative count: **0**.
- WRITE: 100 ns on 506,067; 110 ns on 269,417. Negative count: **0**.

This is correct 68000 retirement. It does **not** discriminate read from write,
which makes it the wrong axis for the read/write comparison and the *right* axis
for a separate replacement-CPU bus-discipline test.

## Strobes

### `/UDS` — a correction to an earlier summary

On the **floppy read** population, `/UDS` is measured **INACTIVE (1) at `/AS` on
all 91,500 cycles**. `/LDS` is active on all 91,500.

On the **floppy write** population, `/UDS` is inactive at `/AS` on all 717 and
`/LDS` asserts later.

An earlier private summary stated both that "/UDS is never asserted on read" and
that "/UDS asserted 100%" for floppy reads. Those conflict. The measured levels
are as reported here, and the published scripts print them directly so the claim
can be checked against the data.

### `/LDS` in-cycle behaviour

| | transitions in cycle | first assert | first deassert |
|---|---|---|---|
| READ | 2 on 66,173; 1 on 25,327 | 0 ns on 66,173 | 310 ns on 84,075 |
| WRITE | 2 on all 717 | +120 ns on 348; +130 ns on 369 | 310 ns on 588 |

## R/W setup

| Population | dominant R/W transition relative to `/AS` |
|---|---|
| READ | none in window on 91,499 of 91,500 |
| WRITE | **-10 ns** on 661, -20 ns on 49, 0 ns on 7 |

Write cycles settle R/W late, essentially at the `/AS` edge. A real setup
difference, but a weaker discriminator than the `/LDS` phase shift.

## Address setup

A3, A4 and A5 settle **-50 ns dominant**, with -60 ns second, before `/AS`
falls. Zero in-cycle address changes on acknowledged floppy cycles. Identical
between reads and writes.

This matches textbook 68000 setup behaviour and is a useful positive check that
the address probes are sound.

## Burst structure

| Capture | Bursts (>3 us gap) | Largest recurring |
|---|---|---|
| READ | 108 (34 of exactly 5 cycles; 67 large) | 2,350 / 2,350 / 2,349 x7 |
| WRITE | 114 (26 of 5; 30 of 7; 12 of 8; 10 of 9) | 8,128, 8,126, 3,701, then 2,351, 2,350, 2,349... |

The **~2,349 cycle burst size recurs in both directions of transfer**, alongside
two much larger 8,128/8,126 bursts in the write capture. A block size that
survives both read and write workloads is unlikely to be workload-specific.

Intra-burst `/AS` fall-to-fall delta is 2290-2300 ns dominant. With C16M at
63.828 ns, 2300 ns = 36.04 C16M cycles — very close to an integer 36, which is
what a processor-cycle-paced poll loop should produce. *Not asserted as a
cycle count; the closeness is noted, not claimed.*

Neither capture contains a burst composed purely of write cycles. Writes are
interspersed into read-dominated traffic.

## Ranked discriminators for future replacement-CPU comparison

Ranked by discriminating power x independence from register decode.

1. **`/LDS` assertion phase** — 0 ns on reads, +120/+130 ns on writes. 100%
   separation, decode-independent. **Primary comparator.**
2. **`/LDS` active-at-`/AS` rate** — 100% of reads, 0% of writes. Binary,
   trivially automated.
3. **Write-cycle T1 tail** — writes show a rare 110 ns `/DTACK` (1.39%) that
   reads do not.
4. **R/W setup latency** — writes settle at -10 ns; reads stable well before.
5. **Write-cycle count in a fixed workload** — 0 vs 717. Confirms a capture
   actually performed writes rather than silently failing to.
6. **Burst size ~2,349** — workload-shape check, not a timing comparator.
7. **`/DTACK` release ordering** — 100-110 ns after `/AS` rises. Identical read
   and write, so **not** a read/write discriminator, but the best available test
   of whether a substituted CPU reproduces stock bus discipline.
8. **DACK static** — identical both directions. Not a read/write discriminator,
   but a strong stock-vs-replacement comparator on that channel.

## What this does not establish

This baseline establishes what stock hardware looks like in both directions, so
that a later difference can be attributed to the CPU-substitution configuration
rather than to the workload. **It does not discriminate between the competing
failure hypotheses.** Those remain open.
