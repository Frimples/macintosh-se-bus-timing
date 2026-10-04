# Evidence policy

## Purpose

This dataset exists to be *checkable*. That only works if a reader can tell,
for every claim, whether it is a measurement, a derivation, someone else's
documented statement, or a guess. The labels below are used strictly.

## The labels

**OBSERVED MEASUREMENT**
A value computed directly from a captured waveform by a script in this
repository. Reproducible from the shipped captures.

*Test:* run the script.

**DERIVED RESULT**
Computed from observed measurements by a stated, deterministic step — a
difference, a ratio, a histogram. The step is written out.

*Test:* check the arithmetic against the cited measurements.

**DOCUMENTED EXTERNAL FACT**
A statement from a cited manufacturer document. Not measured here.

*Test:* check the citation. Apple, Motorola and NCR documents are referenced by
title and page. **No third-party document is reproduced in this repository** —
only the citation and, where needed, a short quotation.

**ENGINEERING INFERENCE**
A conclusion drawn from measurements which follows from them but is not itself
directly measured. The reasoning is stated so it can be challenged.

*Test:* assess whether the reasoning is sound, not just whether the premises are.

**HYPOTHESIS**
A proposed explanation requiring further evidence. **Never** presented as a
finding, and never used to support a conclusion.

*Test:* it should be obvious that it is unproven.

**UNRESOLVED**
A question the data cannot answer. Stated as such rather than guessed at.

*Test:* it should be obvious that nobody knows.

## Rules

1. **A measurement never becomes a conclusion by repetition.** Restating a
   number more confidently does not add evidence.

2. **Correlation is not causation.** Two signals co-occurring in a capture does
   not establish a mechanism. The SCSI LONG/DRQ question is the worked example:
   the timing is measured, the mechanism is unresolved, and the two are never
   merged.

3. **A null channel is not a null result.** A signal that never transitions
   cannot support "no correlation". It supports "no correlation could be
   computed". These are different, and the difference is load-bearing.

4. **Plausible behaviour is not proof of placement.** A channel showing the
   right kind of activity is consistent with correct probing; it does not prove
   continuity to a specific pin. Both statements appear in this repository and
   they mean different things.

5. **Provenance gaps stay open.** Where the physical wiring of a historical
   capture cannot be established, that is recorded as unresolved. It is not
   resolved by inference from a later capture, and it is not resolved by
   guessing which explanation is more likely.

6. **Model-specific evidence does not transfer.** This is a Macintosh **SE**.
   SE/30, Plus and Classic behaviour is not substituted for it anywhere. Where a
   SE differs from a sibling — SCSI support, for instance — the difference is
   stated. Emulator behaviour is never used as evidence of physical hardware
   behaviour.

7. **Emulators are not evidence of hardware.** Noted separately because it is a
   recurring temptation.

8. **Corrections are visible.** When an analysis changes, the original is
   retained and the correction appended. See `docs/corrections-and-errata.md`.
   Silently rewriting an inconvenient number is not permitted, in this
   repository or in the private analysis behind it.

## What this dataset deliberately does not contain

- **No failure hypotheses presented as conclusions.** The dataset is a stock
  reference. The replacement-CPU investigation that motivates it is a separate
  future stage, and none of its open questions are closed here.
- **No proprietary material.** No schematics, ROM images, disk images, manuals,
  magazine scans or commercial software. Citations only. See `LICENSE` and
  `references/SOURCES.md`.
- **No private paths, credentials, or machine-specific identifiers** in anything
  published here.
- **No over-precise claims.** With 10 ns quantisation, nothing finer than 10 ns
  is claimed, and every small-population figure carries its count.

## For contributors

If you add a measurement:

- state which label it carries;
- ship the script that produces it;
- validate it against an independent expected value;
- record its population size, especially if small;
- if it contradicts something already published, add an erratum — do not edit
  the original claim.
