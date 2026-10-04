# Stock Macintosh SE bus-timing baseline

**Reproducible measured reference data for a stock Macintosh SE (MC68000) system
bus.**

This dataset contains logic-analyser captures of a stock Macintosh SE performing
normal work, and the measurements derived from them. It exists so that anyone
building a replacement-CPU or bus-interception system for this machine has an
accurate picture of **what correct hardware does** before they compare their work
against it.

It is a **stock reference only**. It contains no accelerator results and no
failure analysis.

---

## What was measured

A stock Macintosh SE logic board, MC68000 at 8 MHz, observed with a Kingst LA2016
16-channel logic analyser at 100 MHz (10 ns quantisation), ground on PDS pin
B29, with sixteen bus signals probed at the PDS connector:

`C16M`, `/AS`, `/DTACK`, `DRQ`, `R/W`, `/UDS`, `/LDS`, `DACK`, `A23`-`A19`,
`A5`-`A3`.

Four workloads: floppy read, floppy write, idle, SCSI read.

## Why this dataset exists

Work on replacement processors and bus interceptors for the Macintosh SE needs a
**stock baseline** to compare against. Without one, a difference observed on a
modified system cannot be attributed: it might be the modification, or it might
be ordinary behaviour that was never characterised.

The point of publishing the stock baseline **first** is that any later
difference can then be attributed to the configuration rather than to the
workload or to a misremembered assumption.

## Headline results

All OBSERVED MEASUREMENT, re-derived from the shipped captures.

**Processor clock.** C16M = **15.6671 MHz**, period 63.83 ns, measured three
independent ways (rising-to-rising, falling-to-falling, transitions/2/duration),
all agreeing to within 0.00001 MHz. Matches Apple's documented 15.6672 MHz.

**Bus timing.** `/AS`-to-`/DTACK` is **90 ns or 100 ns** on floppy traffic. The
`/AS` cycle is 310 ns or 320 ns. `/DTACK` releases **100-110 ns after `/AS`
rises**, never before — on every acknowledged cycle.

**The primary result — a clean read/write discriminator.**

On a stock SE, the `/LDS` data strobe is **active at `/AS` assertion for a
floppy read** and **inactive at `/AS` assertion for a floppy write**, asserting
120-130 ns later:

| | `/LDS` active at `/AS` | first assertion |
|---|---|---|
| READ (91,500 cycles) | **100%** | 0 ns, or already active |
| WRITE (717 cycles) | **0%** | +120 / +130 ns |

**100% separation, zero overlap.** And critically it is **decode-independent**:
it needs no register identification and no address interpretation, so it can be
measured on any capture where the floppy bus is active.

> **The "write" capture is 98.85% reads.** 717 of 62,433 floppy-window cycles are
> actual writes; the rest are reads. Enough to establish the discriminator, not
> enough to characterise write timing distributions. Read
> `docs/stock-floppy-read-write.md` before quoting write figures.

**SCSI baseline status: partial.** Two timing populations are measured — FAST
90-100 ns and LONG 1110-1130 ns — and the LONG class is tightly quantised to
16.004 C16M periods with a metronomic F-L-L-L motif. Its **mechanism is
UNRESOLVED**, as is its relationship to DRQ, which is a null channel in that
capture. **No register-level claim is published**; the address mapping that would
be needed is known implausible and is documented as an open question.

## Repository layout

```
README.md                  this file
LICENSE                    terms for original content
CONTRIBUTING.md            how to add or correct a measurement
docs/
  methodology.md           how measurements were produced; evidence vocabulary
  hardware-setup.md        machine, analyser, probes, capture inventory
  probe-map.md             channel map and CH7 provenance  <- READ THIS ONE
  stock-bus-baseline.md    the shared timing baseline
  stock-floppy-read-write.md  the primary result
  stock-scsi.md            SCSI measurements and stated gaps
  corrections-and-errata.md   five corrections, including two of our own errors
  evidence-policy.md       what each evidence label means
captures/stock/{idle,floppy-read,floppy-write,scsi-read}/
                           original .sr captures, unmodified
data/stock/
  hashes.sha256            SHA-256 for every shipped capture
  *-summary.csv            per-capture measurement summaries
  floppy-read-vs-write.csv the discriminator, machine-readable
scripts/                   the tools that produced everything here
references/SOURCES.md      cited sources (citations only, no documents copied)
```

## Reproducing the results

```
git clone <this repository>
cd macintosh-se-bus-timing
bash scripts/reproduce.sh
```

Requires Python 3 and NumPy. **No sigrok installation is needed** —
`scripts/sr_to_arrays.py` reads the sigrok `.sr` container directly. (The usual
`sigrok-cli -I sigrok` route fails on builds without the srzip input module, so
a direct reader is provided and was validated against the VCD path on all 16
channels.)

Expected output:

```
C16M                15.6671 MHz  (period 63.83 ns)
floppy READ cycles  91500
floppy WRITE cycles 62433 (717 writes = 1.15%)
/LDS active at /AS  100% of reads, 0% of writes
```

Intermediates land in `work/` (gitignored).

## Provenance and corrections

**Raw captures are published byte-for-byte as acquired, including known
metadata errors.** Channel-name corrections are applied at analysis time via
`--rename`, never by editing a capture. See `docs/probe-map.md`.

The single most important provenance item: **CH7 is physically DACK, not PMCYC.**
Several captures' metadata says `PMCYC`; that label is wrong and **PMCYC was
never captured**. The correct interpretation and the per-capture status —
including one capture whose CH7 identity is genuinely **ambiguous** — are in
`docs/probe-map.md`.

`docs/corrections-and-errata.md` records five corrections, including two
analysis errors of ours (a clock measurement taken as the half-period, and a VCD
parser that silently returned zero transitions). Both were caught by external
validation before publication and neither changed a published finding. They are
recorded because a dataset that hides its own corrections cannot be checked.

## Limitations

- **D0-D15 data bus not probed.** No data-value claim is testable. The mechanism
  behind the `/LDS` result is inference, not measurement.
- **A0 not probed.** The byte-lane question is unresolved.
- **A18-A6 not probed.** Register identification is impossible; only coarse
  address windows can be isolated.
- **E, /VMA, /VPA, PMCYC, IPL not probed.**
- Everything is quantised to **10 ns**.
- System software version, exact media and host application are not recorded.
- **Macintosh SE only.** SE/30, Plus and Classic behaviour is not substituted.

## Future work

The intended next stage, **not** part of this dataset: capture the same channel
map on a replacement-CPU configuration and compare against these numbers.

Ranked metrics for that comparison:

1. **`/LDS` assertion phase** — 0 ns on reads, +120/+130 ns on writes. Primary
   comparator.
2. **`/DTACK` release ordering** — must release 100-110 ns after `/AS` rises.
   Best available test of whether a substituted CPU reproduces stock bus
   discipline. Does *not* discriminate read from write.
3. **DACK activity** — static on stock in both directions, so any activity is an
   immediate contrast.
4. **Burst size ~2,349 cycles** — confirmed in both transfer directions;
   workload-shape check.

Two measurement gaps should be closed before that stage, since they currently
limit interpretation of result 1: **probe A0**, and resolve the **SCSI
register-select mapping** by probing A2/A1/A0 **at the AM5380 chip pins** rather
than at the PDS.

## Status

Stock reference baseline. Floppy read/write results are complete and
reproducible. SCSI results are partial with named gaps. No accelerator or
replacement-CPU measurements are included, and no failure hypotheses are
presented as conclusions.

## Licensing

Original content in this repository is MIT licensed — see `LICENSE`. **No
Apple, Motorola or NCR material is reproduced here.** Third-party product names
and cited specifications remain the property of their respective owners.
