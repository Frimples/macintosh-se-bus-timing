# Probe map and CH7 provenance

## Current physical channel map

All captures in this dataset used the same 16-channel assignment:

| CH | Signal | Notes |
|---|---|---|
| 0 | C16M | Processor clock, 15.6671 MHz measured |
| 1 | /AS | Address strobe, active-low |
| 2 | /DTACK | **System** bus acknowledge, active-low |
| 3 | DRQ | AM5380 pin 22 (SCSI DMA request) |
| 4 | R/W | Read/write direction. 1 = read, 0 = write |
| 5 | /UDS | Upper data strobe, active-low |
| 6 | /LDS | Lower data strobe, active-low |
| 7 | **DACK** | SCSI DMA acknowledge — see provenance below |
| 8 | A23 | |
| 9 | A22 | |
| 10 | A21 | |
| 11 | A20 | |
| 12 | A19 | |
| 13 | A5 | |
| 14 | A4 | |
| 15 | A3 | |
| GND | PDS B29 | |

The map deliberately does **not** include the 68000 address lines A0-A2 in a
form that could be confused with AM5380 chip pins. See the namespace warning
below.

## CH7 provenance — read this before using channel 7

### The physical signal

CH7 was physically clipped to **DACK**, the SCSI DMA acknowledge line. This was
confirmed by the operator after the fact.

**CH2 and CH7 are two different acknowledge signals.** CH2 (`/DTACK`) is the
68000 system bus acknowledge. CH7 (`DACK`) is the SCSI DMA acknowledge. They are
not duplicates of one another and neither is a copy of the other.

### The metadata error

The acquisition commands for the historical captures **incorrectly specified
`CH7=PMCYC`**. Consequently:

- the `probe8=` line in the embedded `.sr` metadata of those captures reads
  `PMCYC`;
- the `$var` header in their VCD exports reads `PMCYC`;
- **the electrical waveform on CH7 is nonetheless DACK.**

This is a labelling error, not invalid electrical data. The captured waveforms
are valid.

**PMCYC was NOT CAPTURED on any capture in this dataset.** No PMCYC timing or
phase claim can be derived from CH7, and none is made here.

### Original files are not modified

The `.sr` and `.vcd` files shipped in `captures/` are byte-for-byte as
acquired, with the incorrect `PMCYC` label intact. That label is evidence of
what the acquisition software was told. The correction is applied at load time:

```
python3 scripts/sr_to_arrays.py CAPTURE.sr OUTDIR --rename PMCYC=DACK
```

`scripts/reproduce.sh` does this for both floppy captures.

### Per-capture status

| Capture | Acquisition metadata says | Physical CH7 | Basis |
|---|---|---|---|
| `idle/` | PMCYC | **AMBIGUOUS** | pre-dates the correction; not established |
| `scsi-read/` (16:17:47, `a5a3-drq`) | PMCYC | **AMBIGUOUS** | see below |
| `scsi-read/` (17:28:27, `drq-dack`) | DACK | DACK | metadata already correct; filename and static CH7 both consistent |
| `floppy-read/` (17:57:50) | PMCYC | DACK | operator-confirmed |
| `floppy-write/` (18:00:41) | PMCYC | DACK | operator-confirmed |

### Why the 16:17:47 SCSI capture remains AMBIGUOUS

That capture's CH7 shows **642,825 transitions — it is live**. The move from
PMCYC to DACK was never placed on a timeline, and the operator confirmation
covered the "recent" acquisitions without stating a boundary time.

A live signal is consistent with **either** net. CH7 being active during SCSI
read activity is equally what PMCYC would do and what DACK might do. So this
capture's CH7 physical identity **cannot be established from the data**, and this
repository does not claim it.

Concretely: no published number in this repository depends on the physical
identity of CH7 in that capture. The SCSI timing and address observations rest
on A23:A19, A5:A3, /AS, /DTACK, /UDS, /LDS and C16M. The CH7 channel is treated
as a null channel for that capture and is not interpreted.

**Do not retroactively reinterpret it.** If the boundary time is ever
established from the operator's own records, this note should be updated in the
same way — by amendment, not by silent rewrite.

## Observed CH7 / DACK behaviour

| Capture | CH7 transitions | Level |
|---|---|---|
| floppy-read (500 ms) | 0 | static high |
| floppy-write (500 ms) | 0 | static high |
| idle (20 ms) | 0 | static high |

**OBSERVED MEASUREMENT.** Across 500 ms of stock floppy reading *and* 500 ms of
stock floppy writing, with `/DTACK` acknowledging every cycle, DACK never
transitions and DRQ never transitions.

**What this is not.** It is not evidence that the SE never uses pseudo-DMA. A
static DACK during programmed-I/O floppy activity is *consistent with* no
pseudo-DMA transfer being in progress, but DACK could equally be gated by a
path that does not toggle this net. Documented uses of held `/DTACK` include
DRQ, successive SCC accesses, and video RAM. This is a **negative reference
observation**, valuable as a stock comparator, and nothing more.

**PI-STORM USE.** Because stock DACK is static in both directions, any DACK
activity on a replacement-CPU capture is an immediate, unambiguous contrast.

## Post-fall probe validation

The logic board was accidentally knocked from the bench after the principal
stock captures. A 20 ms sanity capture was taken afterwards.

**OBSERVED:** no two channels shared a net, and no channel showed displacement
onto a neighbour. Four independent tests were used, including exact
timestamp-set intersection across all 120 channel pairs and edge-time offset
distributions. The closest pair set — A21/A20/A19 at 99.9% level agreement —
was investigated and shown to be three distinct nets: seven distinct bit tuples
appear over the full capture, whereas a doubly-clipped net yields one or two.
The apparent lock is explained by the SE memory map (see below).

**OBSERVED:** all signals behaved plausibly except A23, which showed only 8
transitions confined to a 42 microsecond window and was otherwise static.

**The A23 observation is expected behaviour, not a fault.** A settled Macintosh
SE maps RAM at `$000000` and ROM at `$400000`, so A23 is low for essentially all
normal traffic. The 8 transitions were most plausibly a brief excursion above
`$7FFFFF`.

**What the post-fall analysis did and did not prove.** It proved no duplicates,
no neighbour displacement, and plausible behaviour on 15 of 16 channels. It did
**not** prove exact physical placement of every probe — plausibility of
behaviour is a weaker statement than continuity on a specific pin. The operator
has since physically verified the CH8/A23 clip is solidly connected.

## Namespace warning: system address lines vs AM5380 chip pins

These are **different namespaces** and conflating them caused a major
interpretive error in the private analysis that preceded this dataset.

- **System/CPU address lines** A0-A23 are Macintosh motherboard bus signals.
- **AM5380 chip pins** A0-A2 are the NCR 5380's own three-bit register-select
  input.

For the Macintosh SE the established trace is:

```
system A5  ->  AM5380 A2
system A4  ->  AM5380 A1
system A3  ->  AM5380 A0
```

An earlier assumption that system **A0:A2** select the AM5380 registers was
**incorrect** for the SE and is not used here.

**This dataset publishes no register-level claim.** For completeness, the
reading A5:A3-as-register-index produces implausible results — register index 4
on ~100% of one timing class and odd indices never observed at all — and is
recorded as an open question, not a finding. See `docs/stock-scsi.md`.
