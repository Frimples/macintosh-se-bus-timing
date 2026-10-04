# Stock SCSI baseline — partial, with stated gaps

This section publishes stock SCSI measurements **only where provenance is
strong**. Several questions are explicitly UNRESOLVED, and the gaps are stated
rather than smoothed over.

**Reproducibility caveat.** The SCSI figures here come from the private
analysis of the shipped capture. The scripts in this repository reproduce the
floppy and clock results end-to-end; the SCSI region analysis is not yet
packaged. The numbers below are labelled accordingly.

## Captures

| Capture | Duration | CH7 metadata | CH7 physical |
|---|---|---|---|
| `scsi-read-...a5a3-drq-100mhz-20m.sr` | 20 ms | PMCYC | **AMBIGUOUS** |
| `scsi-read-...drq-dack-a5a3-100mhz-20m.sr` | 20 ms | DACK | DACK |

See `docs/probe-map.md` for why the first capture's CH7 identity is
unresolved and is not claimed.

## Device select region

**DOCUMENTED EXTERNAL FACT.** Apple, *Guide to the Macintosh Family Hardware*,
2nd ed., Figure 3-3, marks `$580000-$5FFFFF` as the SCSI device-select region on
the Macintosh SE.

Note this differs from the Plus. Apple warns that device-select addresses vary
between families, so the Plus mapping is not imported.

## Timing classes — OBSERVED MEASUREMENT

Two distinct `/AS`-to-`/DTACK` populations appear in the SCSI region:

| Class | Range | Count | Share |
|---|---|---|---|
| FAST | 90-100 ns | 22,988 | ~26% |
| LONG | 1110-1130 ns | 67,904 | ~74% |

Across 39,503 complete cycles in the device-select region, all 39,503 received
`/DTACK`; zero unacknowledged, zero orphan `/DTACK`.

### The LONG class is tightly quantised

**OBSERVED MEASUREMENT.**

- LONG - FAST = **1021.5 ns**
- = **16.004 C16M periods** (63.828 ns)
- = **2.003 PMCYC quanta**
- LONG spread across all samples: **under one C16M period** (20 ns total)
- A metronomic FAST, LONG, LONG, LONG loop repeats **9,710 times**
  (9,130 LONG cycles = 9,710 x 3), interleaved with 9,636 FAST runs of 1
- `/AS` and `/DTACK` edge phase relative to C16M is identical in both classes

This is strong evidence about the **timing**. It is not evidence about the
**mechanism**. A long-acknowledge interval that is an exact integer multiple of
both the processor clock and the memory-cycle clock, with sub-period spread and
a metronomic motif, indicates the interval is synchronised to a state machine
driven by those clocks. It does not identify which state machine or why.

## DRQ — UNRESOLVED

**OBSERVED MEASUREMENT.** DRQ (CH3, AM5380 pin 22) shows **one transition in
the entire capture**, at t=0 — the initial state dump. Level 1 at every sample
point on all 39,503 region cycles. The idle control capture is identical.

**Therefore: no correlation between the LONG class and DRQ can be computed
from this data.** This is a null channel, not a measured absence of correlation.

**It must NOT be reported as "the LONG class is DRQ-independent."** That would
be a claim the data cannot support, in either direction. The honest statement is
that the question is unanswerable by construction.

Two hypotheses remain live and are not separated by this data:

1. The machine is not using pseudo-DMA for this read path.
2. DRQ does not toggle in this mode.

These are mechanism questions. A scope with a fine enough timebase can separate
them.

Probe placement was checked and is **not** the explanation: the physical clip at
AM5380 pin 22 was visually confirmed, and a separate oscilloscope measurement on
that physical pin observed a high-level voltage during SCSI activity.

## Address observations

**OBSERVED MEASUREMENT.** Within the SCSI device-select region, all probed
address bits are **stable for the entire bus cycle**. Across all 39,503 region
cycles there are **zero** in-cycle transitions on A3, A4 or A5. The value is
bit-identical at ten sample points from before `/AS` through `/AS`, +10/+20/+50/
+100 ns, before and at `/DTACK`, and through release.

This eliminates "the register-select bits changed mid-cycle and sampling missed
it" as an explanation for anything.

A3 is live on the bus generally — 119,566 high and 122,794 low across 242,360
non-SCSI cycles — and transitions 50-60 ns before `/AS` on exactly the 5,380
cycles whose preceding access had A3 high. That is textbook 68000 setup
behaviour, and it confirms the address probes are sound.

## Register decode — NOT PUBLISHED AS A FINDING

**The register-select mapping for the Macintosh SE is an open question.**

For the SE the established schematic trace is:

```
system A5  ->  AM5380 A2
system A4  ->  AM5380 A1
system A3  ->  AM5380 A0
```

> **Namespace warning.** AM5380 chip pins A0-A2 are the 5380's own register-select
> input. Macintosh system address lines A0-A23 are motherboard bus signals.
> These are different namespaces. Conflating them caused a major interpretive
> error in the private analysis.

An earlier assumption that **system A0:A2** select the AM5380 registers was
**incorrect** for the SE and is not used.

**Why no register claim is published.** Decoding A5:A3 as a register index
produces implausible results:

| index | cycles | share |
|---|---|---|
| 4 | 38,844 | 98.35% |
| 0 | 380 | |
| 2 | 275 | |
| 6 | 4 | |
| odd indices (1, 3, 5, 7) | **0** | **never observed** |

A real three-bit register-select field under a mix of polling and data transfer
should show a **range** of indices in both timing classes. Instead one class is
100% homogeneous at index 4, and half the address space is never touched at all.
A5 is high on 38,848 of 39,503 cycles and A4 on only 279.

That is **KNOWN IMPLAUSIBLE**. Two explanations remain live and cannot be
separated by these captures:

- **E1** the probed A3 net is not the net driving AM5380 A0.
- **E2** the register-decode assumption itself is wrong.

Both the LONG and FAST classes are pure with respect to the A5:A3 field, which
sharpens the puzzle rather than resolving it.

**Consequence.** Any earlier register-level attribution of SCSI cycles is
**unavailable on current evidence**. Before any of it is relied on, the
resolution step is to probe A2/A1/A0 **at the AM5380 chip pins**, not at the
PDS. If E1 holds, all register-level conclusions from these captures are void
regardless of further capture work. That measurement gates everything else here.

## Summary table

| Observation | Status |
|---|---|
| Device-select region `$580000-$5FFFFF` | DOCUMENTED EXTERNAL FACT |
| FAST 90-100 ns, LONG 1110-1130 ns populations | OBSERVED MEASUREMENT |
| LONG is an exact multiple of C16M and PMCYC quanta | OBSERVED MEASUREMENT |
| Metronomic F-L-L-L loop, 9,710 repetitions | OBSERVED MEASUREMENT |
| Address bits stable through every SCSI cycle | OBSERVED MEASUREMENT |
| LONG mechanism | **UNRESOLVED** |
| LONG / DRQ relationship | **UNRESOLVED — null channel, cannot be computed** |
| Register-select mapping | **UNRESOLVED — A5:A3 reading known implausible** |
| CH7 physical identity (16:17:47 capture) | **UNRESOLVED — ambiguous provenance** |
