# Methodology

How these measurements were produced, so that a reader can trust them, repeat
them, or disagree with them on the basis of something checkable.

## 1. Evidence vocabulary

Every claim in this repository carries one of these labels. They are used
strictly, and the distinctions are the point of the dataset.

| Label | Meaning |
|---|---|
| **OBSERVED MEASUREMENT** | A number computed directly from a captured waveform. Reproducible from the shipped captures with the shipped scripts. |
| **DERIVED RESULT** | A value computed from observed measurements by a stated, deterministic step (a difference, a ratio, a histogram). |
| **DOCUMENTED EXTERNAL FACT** | A statement from a cited manufacturer document. Not measured here. |
| **ENGINEERING INFERENCE** | A conclusion drawn from measurements, which follows from them but is not itself directly measured. |
| **HYPOTHESIS** | A proposed explanation that would need further evidence. Never presented as a finding. |
| **UNRESOLVED** | A question the data cannot answer. Stated as such rather than guessed at. |

The separation between OBSERVED MEASUREMENT and ENGINEERING INFERENCE is the
one most often lost in this kind of work. A timing population is a measurement.
Its *mechanism* is not, unless separately demonstrated.

## 2. Machine under test

- **Macintosh SE**, stock logic board, MC68000 (8 MHz, 16-bit data bus),
  1 MB RAM, Integrated Workbench Machine (IWM) floppy controller.
- **NOT** an SE/30. The SE/30 has ADB, a SuperDrive-capable controller, and
  different video/sound; none of its behaviour is imported here. Where SE and
  SE/30 differ, this dataset describes the SE only.
- One known deliberate exception is stated where it occurs: the SE's SCSI
  support is an add-on card, and its bus behaviour differs from a Plus. That is
  recorded, not generalised.
- System software version during capture is **not recorded** and is a known
  limitation. See `docs/hardware-setup.md`.

## 3. Acquisition

- **Logic analyser:** Kingst LA2016, 16 channels.
- **Sample rate:** 100 MHz, i.e. one sample per 10 ns.
- **Ground:** PDS pin B29.
- **Trigger:** free-running; captures are time-windowed, not triggered on a
  specific bus event.
- **Container:** sigrok `.sr` (srzip), exported to VCD for the original
  analyses. The `.sr` files are the archival originals and are shipped
  unmodified.

### Quantisation — the dominant uncertainty

Every timestamp in this dataset is quantised to **10 ns**. The C16M clock
period is 63.83 ns, which does not divide evenly into 10 ns. Two consequences
must be understood before reading any number here:

1. **Clock periods dither.** A 63.83 ns period appears in the raw period
   histogram as alternating 60 ns and 70 ns intervals. This is expected and is
   not jitter or instability. The mean over many edges recovers 63.83 ns.
2. **Edge timing has +/-10 ns of quantisation error.** Two measurements that
   differ by less than 10 ns cannot be distinguished. Where this dataset reports
   an offset like "+120/+130 ns", both values are the same physical edge seen
   either side of a sample boundary. It is one event, not two.

Any claim in this repository that depends on resolving less than 10 ns is
flagged as UNRESOLVED rather than asserted.

## 4. Active-low signal interpretation

Four captured signals are active-low: `/AS`, `/DTACK`, `/UDS`, `/LDS`.

**Polarity is NOT inferred from the signal names.** A VCD header produced by
sigrok does not carry any negation marker: sigrok strips the leading slash, so
the header of a capture on `/LDS` reads `LDS`. Reading names to determine
polarity is a known failure mode in this project that produced a false
conflict twice before it was caught.

Polarity was established instead from established SE bus behaviour and then
corroborated against the data. The corroboration is visible and checkable:
`/DTACK` is observed to release **100-110 ns after** `/AS` rises on every
acknowledged cycle, never before. That ordering is only correct if `/AS` and
`/DTACK` are read as active-low. If either were misread, the release would
appear to precede the assertion. The scripts therefore report
`/LDS` level `0 = ACTIVE`, and every "active at /AS" statement means "low".

`DACK` (channel 7) is **not** active-low in the published sense. It is a
separate acknowledge line; see `docs/probe-map.md`.

## 5. Channel-name corrections are supplied at load time, never in the capture

Several historical captures embed a channel label that is known to be wrong.
The raw files are preserved byte-for-byte exactly as acquired; the correction is
applied when the data is loaded:

    python3 scripts/sr_to_arrays.py CAPTURE.sr OUTDIR --rename PMCYC=DACK

This is deliberate. Editing a capture to "fix" its metadata would destroy the
only record of what the acquisition software was actually told, which is itself
evidence. The correction lives in the analysis layer, where it is visible.

`docs/corrections-and-errata.md` records every correction, including the two
that were errors in the original private analysis.

## 6. Cross-validation of the container reader

`scripts/sr_to_arrays.py` reads the sigrok `.sr` container directly. This was
necessary because the `sigrok-cli` build on the reference host (0.6.0) lacks
the srzip input module, so `-I sigrok` fails and the usual VCD export path is
not reproducible there.

Because the container layout (2 bytes per sample, LSB-first bit packing, probe
order from the `probeK=` metadata lines) was determined empirically, it was
**validated rather than assumed**: the same capture was decoded both ways — once
natively from `.sr`, once via the VCD path — and all 16 per-channel transition
counts were compared. All 16 matched exactly. That check validates the bit
packing and channel ordering, not merely the sample count.

## 7. Statistical honesty

- Histograms are reported with exact populations, not rounded summaries.
- Where a population is small (the 717 write cycles, the 25-cycle 110 ns tail),
  the count is stated so the reader can judge it. Small populations are not
  treated as characterisations.
- Percentages are given to two decimal places at most.
- No smoothing, no outlier removal, no fitting.
- Every script is deterministic. No randomness, no thresholds that were tuned
  after seeing the result.

## 8. Known limitations of the channel set

The 16-channel map is a compromise, and these gaps are hard limits — they are
not addressed by re-running the same captures.

| Not captured | Consequence |
|---|---|
| D0-D15 data bus | No data-value claim is testable. Any mechanism explanation of strobe behaviour is inference only. |
| A0 | The byte-lane question is unresolved; the lane conclusion rests on strobes, not measurement. |
| A18-A6 | 16 of 24 address bits unknown. Register identification is impossible; only coarse address windows can be isolated. |
| E, /VMA, /VPA | No E/acceptance cycle can be verified. |
| PMCYC | Never captured on these captures (see `docs/probe-map.md`). No phase or cycle-count reference is available. |
| IPL, /SYNQ | Interrupt handshake cannot be observed. |

A0 and the data bus are the two gaps that most directly limit interpretation of
the primary result. Adding A0 is a single probe and would convert an inference
into a measurement.
