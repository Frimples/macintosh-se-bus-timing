# Hardware setup

## Machine under test

| | |
|---|---|
| Model | **Macintosh SE** |
| CPU | Motorola MC68000, 8 MHz |
| Data bus | 16-bit |
| Address bus | 24-bit |
| RAM | 1 MB (4x SIMM, paired) |
| Floppy controller | Integrated Workbench Machine (IWM) |
| Logic board | Stock, unmodified |
| Logic board ground | PDS pin B29 |

**This is not an SE/30.** The SE/30 has ADB, a different video and sound
subsystem, and different controller capability. None of its behaviour is
imported anywhere in this repository.

The Macintosh SE also has no built-in SCSI; it uses an add-on card, and its bus
behaviour differs from a Macintosh Plus. Where that matters it is stated
explicitly rather than generalised.

## Logic analyser

| | |
|---|---|
| Device | Kingst LA2016 |
| Channels | 16 |
| Sample rate | 100 MHz (one sample per 10 ns) |
| Trigger | free-running, time-windowed |
| Container | sigrok `.sr` (srzip), exported to VCD for analysis |
| Software | libsigrok 0.6.0-git-0bc24877 |

## Probe configuration

Channel assignment is in `docs/probe-map.md`. Ground is PDS B29.

Probes were attached to the **PDS connector** (Processor Direct Slot) rather
than to logic-board component pins, with the exception of:

- **DRQ** — probed directly at **AM5380 pin 22**, on the SCSI card.

> **Why this matters for interpretation.** Because the address lines were probed
> at the PDS rather than at the controller chip, it has not been established
> that the probed A3 net is the net driving the AM5380's A0 pin. This is an open
> question with real consequences for register-level claims — see
> `docs/stock-scsi.md`.

## Capture inventory

| Directory | Capture | Acquired | Samples | Duration |
|---|---|---|---|---|
| `captures/stock/floppy-read/` | `stock-se-floppy-read-16ch-a5a3-drq-100mhz-50m.sr` | 2026-10-03 17:57 | 50,001,545 | 500.015 ms |
| `captures/stock/floppy-write/` | `stock-se-floppy-write-16ch-a5a3-drq-100mhz-50m.sr` | 2026-10-03 18:00 | 50,001,553 | 500.015 ms |
| `captures/stock/idle/` | `stock-se-idle-16ch-a5a3-drq-100mhz-2m.sr` | 2026-10-03 16:13 | 2,000,000 | 20.000 ms |
| `captures/stock/scsi-read/` | `stock-se-scsi-read-16ch-a5a3-drq-100mhz-20m.sr` | 2026-10-03 16:17 | 20,000,000 | 200.015 ms |
| `captures/stock/scsi-read/` | `stock-se-scsi-read-16ch-drq-dack-a5a3-100mhz-20m.sr` | 2026-10-03 17:28 | 20,000,000 | 200.015 ms |

All capture the same machine and the same probe set. Hashes in
`data/stock/hashes.sha256`.

## Workloads

- **floppy-read** — reading a floppy disk on a write-protected disk. Produces
  read traffic only in the floppy window.
- **floppy-write** — writing to a freshly formatted, writable disk. **98.85% of
  the floppy-window traffic in this capture is still reads**; see
  `docs/stock-floppy-read-write.md`.
- **idle** — machine at rest.
- **scsi-read** — reading from a SCSI device on the add-on card.

Exact disk, drive unit and host application are **not recorded** and are a known
limitation. See Limitations below.

## Post-fall probe validation

The logic board was knocked from the bench after the principal captures. A
sanity capture was taken afterwards (`stock-se-post-fall-probe-check-100mhz-2m.sr`,
2026-10-03 18:35) and is **not published here** — it was a validation artefact,
not a dataset capture.

Findings: no duplicate clips and no neighbour displacement across all 120
channel pairs; all signals behaved plausibly except A23, which showed little
activity — expected, since a settled SE maps RAM at `$000000` and ROM at
`$400000`, so A23 is low for normal traffic. The operator has since physically
verified the A23 clip is solidly connected. Detail in `docs/probe-map.md`.

## Limitations

Stated plainly, because they bound what this dataset can be used for.

**Not recorded**

- System software version during capture.
- Exact floppy disk, drive unit, host application, or SCSI device model.
- Ambient conditions or supply voltage.
- Whether the machine had any expansion installed beyond the SCSI card.

**Not captured** — see the full table in `docs/methodology.md` §8. The two that
matter most:

- **D0-D15 data bus.** No data-value claim is testable. The mechanism behind the
  primary `/LDS` result is therefore inference, not measurement.
- **A0.** The byte-lane question is unresolved; that part of the interpretation
  rests on strobe behaviour rather than on the address line itself.

**Model scope**

- Results describe a stock Macintosh SE only. Do not generalise to the Plus,
  SE/30 or Classic.
- Where the SE differs from a sibling model, the difference is stated rather
  than smoothed over.

**Statistical**

- The write population is 717 cycles. Enough to establish the `/LDS` phase
  signature at 100% separation; **not** enough to characterise write-cycle
  timing distributions the way 91,500 read cycles allow.
- All timestamps are quantised to 10 ns. Nothing finer is claimed.
