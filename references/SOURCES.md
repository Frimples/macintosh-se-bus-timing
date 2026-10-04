# Sources

Citations for material **referenced** by this dataset.

**No document listed here is reproduced, bundled, or redistributed in this
repository.** Each was consulted at the location and page given. Readers must
obtain them from their original sources. Product names and cited specifications
remain the property of their respective owners — see `LICENSE`.

## Primary manufacturer documentation

**Apple Computer Inc.** — *Guide to the Macintosh Family Hardware*, 2nd edition,
1990. (Cited in this repository as **[GMFH90]**.)

Used for:

- **Appendix A** — C16M = 15.6672 MHz. This is the reference against which the
  measured 15.6671 MHz was validated.
- **Figure 3-3** — SCSI device-select region `$580000-$5FFFFF` on the Macintosh
  SE.
- General system bus architecture.

**Apple Computer Inc.** — *Designing Cards and Drivers for the Macintosh II and
SE*, 1987. (Cited as **[DCD87]**.)

Used for:

- **Chapter 12, page 12-4** — top 4 MB of the 8 MB SE address space contains the
  IWM and VIA. Basis for the coarse floppy address window.
- **Chapter 12, page 12-5** — power-on RAM placement at `$600000`; after the
  first access anywhere in `$400000-$5FFFFF`, RAM occupies `$000000` while ROM
  remains at `$400000`. Basis for the post-fall A23 interpretation: a settled SE
  has A23 low for normal traffic.

**NCR Corporation** — *AM5380 SCSI Interface Chip Design Manual*, May 1985.

Used for:

- The AM5380's three-bit register-select input, labelled **A0-A2 as chip pins**.
  Referenced only for the namespace distinction; **no register-level claim is
  published** in this dataset. See `docs/stock-scsi.md`.

**Motorola Inc.** — MC68000 series technical documentation.

Referenced generally for 68000 bus protocol. Specific values used here — such as
the requirement that `/DTACK` be released after `/AS` rises — were validated
against the observed captures as well as against documentation, so that the
active-low sense could be confirmed from the data rather than assumed.

## Standards and format references

**sigrok / libsigrok** — capture container format (`.sr`, srzip) and VCD
export. Captures in this repository are stored in the `.sr` container.

No sigrok source code is included in this repository. sigrok is licensed
separately by its own authors; see <https://sigrok.org/>.

## Sources deliberately NOT used

For the avoidance of doubt, and because these were considered and rejected:

- **Emulator output.** Emulator behaviour is not evidence of physical
  Macintosh SE behaviour and is not used anywhere in this dataset.
- **Macintosh SE/30 documentation**, for anything beyond explicit comparative
  framing. SE/30 behaviour is not substituted for SE behaviour.
- **Macintosh Plus device-select mapping.** Apple warns that device-select
  addresses differ between families, so the Plus mapping is not imported into SE
  analysis.
- **Forum, Reddit and social media.** Used, if at all, only to locate primary
  documents; never as a source for a specification.

## Citation discipline

When adding a source:

1. Prefer primary manufacturer documentation over secondary description.
2. Give enough detail to locate it: title, publisher, edition, year, and page.
3. **Cite; do not copy.** Quote only the minimum needed, and never reproduce a
   document.
4. Distinguish DOCUMENTED EXTERNAL FACT from anything measured here. A reader
   must be able to tell which claims came from a vendor and which came from a
   waveform.

## Citations in the dataset

| Tag | Document | Where used |
|---|---|---|
| [GMFH90] | Guide to the Macintosh Family Hardware, 2nd ed., 1990 | `docs/methodology.md`, `docs/stock-scsi.md`, `docs/stock-floppy-read-write.md` |
| [DCD87] | Designing Cards and Drivers for the Macintosh II and SE, 1987 | `docs/probe-map.md`, `docs/hardware-setup.md`, `docs/stock-floppy-read-write.md` |
| — | NCR AM5380 Design Manual, May 1985 | `docs/probe-map.md`, `docs/stock-scsi.md` (namespace distinction only) |
| — | Motorola MC68000 documentation | `docs/methodology.md` (bus protocol; corroborated against captures) |
