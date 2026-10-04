# Contributing

## What this repository is for

A reproducible reference dataset of measured **stock** Macintosh SE MC68000 bus
behaviour. Contributions that improve its accuracy, reproducibility, or honesty
about its limits are welcome.

## Ground rules

These are not stylistic preferences. They are what makes the dataset usable.

1. **Label every claim.** OBSERVED MEASUREMENT, DERIVED RESULT, DOCUMENTED
   EXTERNAL FACT, ENGINEERING INFERENCE, HYPOTHESIS, or UNRESOLVED. See
   `docs/evidence-policy.md`.
2. **Ship the script.** A number without the code that produces it is not a
   measurement here.
3. **Validate against something external** before publishing a figure. When a
   result is surprising, suspect the analysis first. Five corrections in
   `docs/corrections-and-errata.md` were all caught this way — three of them
   were confidently wrong numbers, not obvious failures.
4. **Never edit a capture.** If a capture's metadata is wrong, apply a rename at
   load time (`--rename PMCYC=DACK`). Editing raw data destroys the only record
   of what the acquisition software was told.
5. **Never rewrite a published number in place.** Add an erratum. The original
   claim stays, with its correction appended.
6. **State small populations.** 717 cycles is enough to establish a 100%-clean
   signature and not enough to characterise a distribution. Say which.
7. **Respect the 10 ns quantisation.** Nothing finer may be claimed.
8. **No proprietary material.** Citations only — no schematics, ROM images, disk
   images, manuals, magazine scans, or commercial software. See `LICENSE`.
9. **Macintosh SE only.** Do not substitute SE/30, Plus, or Classic behaviour.
10. **Emulator output is not hardware evidence.** Never use it as such.

## Adding a measurement

1. Write the script under `scripts/`. Make it deterministic — no randomness, no
   thresholds tuned after seeing the result.
2. Make it fail loudly on bad input. `floppy_rw_discriminator.py` exits non-zero
   if the separation is not clean; `sr_to_arrays.py` can assert that required
   channels are present. A script that cannot fail will eventually report a
   clean-looking wrong answer.
3. Include the bit-order guard if you select an address window. `A23:A19=11011`
   means A23=1 — writing it inverted returns zero cycles while every individual
   term is non-zero. This happened twice.
4. Add the CSV row to `scripts/export_summaries.py` and regenerate.
5. Document it in the relevant `docs/` file, with its population size.
6. If it contradicts something already published, add an erratum rather than
   editing.

## Correcting an existing number

Open `docs/corrections-and-errata.md` and append. Include:

- what the original claim was, verbatim;
- why it was wrong;
- how it was caught;
- the corrected value, with the script that produces it;
- whether any published finding changes.

If the correction changes a headline, update `README.md` **and** the affected
doc, and say in the erratum that you did.

## Capture contributions

If you contribute captures:

- record exact filename, acquisition date/time, workload, sample rate, sample
  count, duration, **physical** probe map, the acquisition metadata map, and
  SHA-256;
- state explicitly whether the acquisition metadata accurately describes the
  physical wiring — and if it does not, say so and supply the correction at
  analysis time;
- if any channel's physical identity is ambiguous, **say so**. Do not resolve
  it by inference from a neighbouring capture. The 16:17:47 SCSI capture in
  this dataset is deliberately left ambiguous for exactly this reason;
- state known limitations, including what was not probed.

Prefer `.sr` over `.vcd`. `.sr` is smaller and is the archival original; the
VCD export is regenerable.

## Checking your work before submitting

- Every number traceable to a script and a capture in this repository.
- Hashes recomputed and matching `data/stock/hashes.sha256`.
- No absolute private paths.
- No credentials, tokens, machine names, or personal identifiers.
- No withdrawn figures — in particular the **31.33 / 31.334 MHz** clock value,
  which was a half-period analysis error.
- Labels applied.
- Population sizes stated for anything under a few thousand cycles.

## Review

Contributions are reviewed against the evidence policy. A well-documented
UNRESOLVED is more valuable than a confident guess, and will be accepted. A
confident guess presented as a measurement will be sent back.

## Licence

By contributing you agree your contribution is licensed under the MIT terms in
`LICENSE`, which covers original repository content only.
