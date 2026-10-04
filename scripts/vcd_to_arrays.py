#!/usr/bin/env python3
"""
vcd_to_arrays.py — convert a sigrok VCD into per-channel transition arrays.

PURPOSE
    Stage 1 of every analysis in this repository. Reads a sigrok-exported VCD
    and writes a compressed .npz holding, for each channel, the timestamp and
    level of every transition. All downstream scripts consume that .npz.

WHY THIS EXISTS INSTEAD OF USING A VCD LIBRARY
    The analyses here are about signal *timing* to 10 ns quantisation, and the
    two published findings (the C16M period and the /LDS read-vs-write phase
    shift) both depend on exact edge placement. A small explicit reader keeps
    that auditable.

    A sigrok .sr file can be converted losslessly to VCD with sigrok-cli, so
    VCD is used as the interchange format (see scripts/README.md).

CORRECTIONS APPLIED IN THIS COPY
    This script is derived from the original private analysis script. Two bugs
    present in the private original are fixed here. Both are recorded in
    docs/corrections-and-errata.md; neither invalidates a published number.

      BUG 1 (VCD timestamp/value-change sharing a line).
          sigrok may emit "#<time> <value changes...>" on ONE line. A reader
          that assumes every "#" line carries only a timestamp silently drops
          every value change on such a line. The original produced ZERO
          transitions on all 16 channels because of this. Fixed: split the line,
          take the timestamp from part 0, then process the remaining parts as
          value changes.

      BUG 2 (symbol lookup keyed by the wrong dictionary).
          The original looked up channel names via the VCD $var *identifier
          map* incorrectly, so some channels were mis-named. Fixed: look up
          via the parsed $var table.

    The private original was NOT modified. Only this copy is corrected.

CHANNEL NAME CORRECTIONS
    The acquisition metadata embedded in several historical .sr/.vcd files
    labels CH7 as "PMCYC". That label is known to be WRONG for the floppy
    captures: CH7 was physically clipped to DACK (SCSI DMA acknowledge), and
    PMCYC was never captured at all. This script does not silently rewrite
    anything -- pass an overrides JSON to rename channels at load time. See
    --channel-map and scripts/README.md. Originals are never modified.

USAGE
    python3 vcd_to_arrays.py INPUT.vcd OUTPUT_DIR [--channel-map MAP.json]
                                            [--expect NAME,...]

    --channel-map  JSON file mapping VCD symbol -> canonical channel name.
                   Example: {"(": "DACK"}. Use this to supply the CH7
                   correction WITHOUT touching the capture.
    --expect       Comma-separated list of channels that MUST be present.
                   Exits non-zero if any is missing. Use to catch a capture
                   that lacks a channel rather than silently analysing fewer.

OUTPUT
    OUTPUT_DIR/tr.npz with arrays ts_<NAME> and vs_<NAME> (int64 / int8).
    OUTPUT_DIR/parse_report.txt with per-channel transition counts.
"""
import json
import os
import sys


def parse_vcd(path, overrides=None, expect=None):
    overrides = overrides or {}
    sym2name = {}
    lines = 0
    ts = {}
    vs = {}
    cur = None
    seen_defs = False
    with open(path, 'r', errors='replace') as fh:
        for raw in fh:
            lines += 1
            s = raw.strip()
            if not s:
                continue
            if not seen_defs:
                if s.startswith('$var'):
                    # $var wire 1 ( DACK $end
                    parts = s.split()
                    sym, label = parts[3], parts[4]
                    sym2name[sym] = overrides.get(label, label)
                elif s.startswith('$enddefinitions'):
                    seen_defs = True
                continue
            if s[0] == '#':
                # FIX (BUG 1): a timestamp line may ALSO carry value changes.
                parts = s.split()
                cur = int(parts[0][1:])
                for tok in parts[1:]:
                    _apply(tok, cur, sym2name, ts, vs)
            elif s[0] in '01':
                _apply(s, cur, sym2name, ts, vs)
            elif s[0] in 'b':
                _apply(s, cur, sym2name, ts, vs)
            elif s[0] in 'r':
                continue  # string values: not produced by sigrok export
    return sym2name, ts, vs, lines


def _apply(tok, cur, sym2name, ts, vs):
    if not tok:
        return
    val, sym = tok[0], tok[1:]
    name = sym2name.get(sym)
    if name is None:
        return
    ts.setdefault(name, []).append(cur)
    vs.setdefault(name, []).append(int(val))


def main(argv):
    if len(argv) < 3:
        sys.stderr.write(__doc__)
        return 2
    src, outdir = argv[1], argv[2]
    overrides, expect = {}, None
    i = 3
    while i < len(argv):
        if argv[i] == '--channel-map':
            overrides = json.load(open(argv[i + 1]))
            i += 2
        elif argv[i] == '--expect':
            expect = [c for c in argv[i + 1].split(',') if c]
            i += 2
        else:
            sys.stderr.write('unknown arg: %s\n' % argv[i])
            return 2

    sym2name, ts, vs, nlines = parse_vcd(src, overrides)
    if expect:
        missing = [c for c in expect if c not in ts]
        if missing:
            sys.stderr.write('MISSING CHANNELS: %s\n' % ','.join(missing))
            return 1

    import numpy as np
    os.makedirs(outdir, exist_ok=True)
    out = {}
    for name, times in ts.items():
        out['ts_' + name] = np.asarray(times, dtype=np.int64)
        out['vs_' + name] = np.asarray(vs[name], dtype=np.int8)
    np.savez_compressed(os.path.join(outdir, 'tr.npz'), **out)

    rep = ['VCD: %s' % src, 'lines: %d' % nlines, '']
    rep.append('%-8s %14s  %s' % ('CHANNEL', 'TRANSITIONS', 'LEVELS'))
    for name in sorted(ts):
        lv = sorted(set(int(x) for x in vs[name]))
        rep.append('%-8s %14d  %s' % (name, len(ts[name]) - 1, lv))
    rep.append('')
    rep.append('applied overrides: %s' % (overrides or 'none'))
    open(os.path.join(outdir, 'parse_report.txt'), 'w').write('\n'.join(rep))
    print('\n'.join(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))