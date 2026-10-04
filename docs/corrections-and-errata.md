# Corrections and errata

Two analysis errors were made during the private analysis that preceded this
dataset. Both were caught before publication. Both are recorded here in full
because a dataset that hides its own corrections cannot be checked.

Neither error changed a published finding. Both produced confidently-stated
wrong intermediate results, which is the reason they are worth writing down.

---

## ERRATUM 1 — C16M reported as 31.33 MHz (withdrawn)

**The error.** The C16M clock was measured as the mean interval between
*consecutive transitions* of the clock signal. For a square wave that is the
**half-period**. A square wave has two transitions per cycle, so this reported a
frequency exactly **2x too high**: 31.3342 MHz for a clock that actually runs at
15.6671 MHz.

**The secondary error.** Having obtained a number that disagreed with every other
capture, the result was labelled a **physical probe anomaly** and escalated as
"the hardest anomaly in the investigation", with cross-capture comparison barred
until explained. It was treated as a hardware fault. It was arithmetic.

**The correction.** Measure using same-polarity edges:

| Method | Result |
|---|---|
| rising-to-rising | 63.8279-63.8281 ns -> 15.6671 MHz |
| falling-to-falling | 63.8279-63.8281 ns -> 15.6671 MHz |
| transitions / 2 / duration | 15.6671 MHz |

All three agree to within 0.00001 MHz on all three captures.

**Reference.** Apple, *Guide to the Macintosh Family Hardware*, 2nd ed.,
Appendix A: C16M = 15.6672 MHz.

**Status: ANALYSIS ERROR RESOLVED.** CH0 did not move. No probe action was
required. The 31.33 / 31.334 MHz figure is **withdrawn** and must not appear
anywhere in published material.

**Consequences that were unnecessarily imposed and are now lifted:**

- cross-capture phase comparison,
- refusal to express the 2290-2300 ns loop period in clock cycles,
- a "re-probe CH0" change to the write-capture procedure.

---

## ERRATUM 2 — VCD parser silently returned zero transitions

**The error.** The VCD reader assumed that a line beginning with `#` carries only
a timestamp. sigrok may emit a timestamp and value changes on the **same line**
(`#0 0! 1"`). On such lines every value change was silently dropped.

**The effect.** The parser reported **zero transitions on all 16 channels** and
ran to completion without error. Had that result been reported as a measurement,
the entire dataset would have been wrong in a way that looked like a working
tool.

**A second bug in the same script.** The symbol-to-channel-name lookup was keyed
incorrectly, mis-naming some channels.

**The correction.** Split the line, take the timestamp from the first field, and
process the remaining fields as value changes; look up names via the parsed
`$var` table. Both are fixed in the published `scripts/vcd_to_arrays.py`.

**Why it is in the errata rather than silently fixed.** A silently-empty parse
is indistinguishable from a quiet signal. Every figure in this dataset was
produced after the fix.

---

## ERRATUM 3 — CH7 interpreted as PMCYC

**The error.** CH7 was analysed as PMCYC throughout the original reports.

**The truth.** CH7 was physically clipped to **DACK** (SCSI DMA acknowledge).
The acquisition commands incorrectly specified `CH7=PMCYC`, so both the `.sr`
metadata and the VCD header carry the wrong name while the waveform is DACK.
**PMCYC was never captured.**

**The correction.** Applied at load time, never by editing captures. See
`docs/probe-map.md`.

**Withdrawn claims.** All PMCYC timing and phase statements from the original
analysis, including "PMCYC is static throughout" and "PMCYC moved 642,825 times
during SCSI". The latter is also **ambiguous provenance** — see below.

---

## ERRATUM 4 — incorrect strobe polarity inference

**The error.** Active-low polarity was inferred from signal names in the VCD
header. sigrok strips the leading slash, so a header on `/LDS` reads `LDS` with
no negation marker. Reading polarity from that produced a false bus-discipline
conflict twice before it was caught.

**The correction.** Polarity is established from documented SE bus behaviour and
then corroborated against the data. The corroboration is checkable: `/DTACK` is
observed releasing 100-110 ns **after** `/AS` rises on every acknowledged cycle,
never before — which is only consistent with both being read active-low.

---

## ERRATUM 5 — address bit-order inversion

**The error.** The floppy-window mask for `A23:A19 = 11011` was written as
`(0, 1, 0, 1, 1)` — A23 inverted. This returned **zero** floppy cycles while
every individual term was non-zero.

**How it was caught.** The partial count after the first three terms, 566,695,
matched the **ROM** block population exactly. That coincidence identified the
inversion immediately.

**The correction.** `A23:A19 = 11011` means A23=1, A22=1, A21=0, A20=1, A19=1.
The published scripts additionally assert that the ROM window is present, so the
inversion now fails loudly instead of returning empty.

**Near-miss note.** A later analysis in the same session re-introduced this
inversion while checking the same data. It was caught the same way.

---

## ERRUMATA — unverified claim in a published draft

**What.** An earlier draft of the post-fall probe validation labelled the
`$000000-$07FFFF` region "low RAM / globals" without citing a source.

**Status.** The label is correct — a settled SE maps RAM at `$000000`
(*Designing Cards and Drivers for the Macintosh II and SE*, p. 12-5) — but it
was asserted before being verified. It is now sourced in `docs/probe-map.md`.

Recorded because an unverified label that happens to be right is still a defect
in method.

---

## Unresolved provenance — CH7 in the 16:17:47 SCSI capture

Not an error: a genuine open question, deliberately not closed.

CH7 in that capture shows **642,825 transitions — it is live**. The move from
PMCYC to DACK was never placed on a timeline, and the operator confirmation
covered "recent" acquisitions without a boundary time. A live signal is
consistent with either net, so **its physical identity cannot be established
from the data**.

This dataset therefore **does not claim** what CH7 physically was on that
capture, and no published number depends on it.

If the boundary is ever established from the operator's own records, this note
should be amended — by adding to it, not by rewriting.

---

## Why these are recorded at all

Three of the five errors produced a *confidently wrong number*, not an obvious
failure. Every one was caught by an external check, not by the analysis itself:

| Error | Caught by |
|---|---|
| C16M half-period | comparing against Apple's documented 15.6672 MHz |
| VCD timestamp bug | a channel cannot be simultaneously live and dead |
| bit-order inversion | an intermediate count matching the ROM block exactly |

The method now adopted, and documented in `docs/methodology.md`:

> **Validate every captured-waveform figure against an independent expected
> value before reporting it as a measurement.** When a result is surprising,
> suspect the analysis before suspecting the hardware.
