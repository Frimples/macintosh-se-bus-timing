#!/usr/bin/env python3
"""
sr_to_arrays.py — read a sigrok .sr capture directly into transition arrays.

WHY NOT JUST USE sigrok-cli
    The obvious route is:
        sigrok-cli -I sigrok -O vcd --input-file capture.sr --output-file out.vcd
    That was attempted while preparing this dataset and FAILED on the reference
    host: the installed sigrok-cli (0.6.0-git-0bc24877) builds WITHOUT the
    srzip input module, so `-I sigrok` returns "Input module 'sigrok' not
    found". The VCD export path used to produce the original analyses therefore
    is not reproducible everywhere.

    This script removes that dependency. It reads the .sr container directly.

CONTAINER FORMAT (verified empirically, not assumed)
    A sigrok .sr file is a ZIP archive containing:
        version              1 byte
        metadata             newline-separated KEY=VALUE text, including
                             "total probes=N" and "probeK=NAME" lines
        logic-1-1            concatenated fixed-width sample rows
        (optionally logic-2-1, logic-3-1 ... for additional channels)

    With 16 channels the sample row is 2 bytes, giving 2 bytes per sample.
    Bits are packed LSB-first within each byte, and probe order follows the
    probeK=NAME lines: probe1 is bit 0 of byte 0, probe2 is bit 1 of byte 0,
    ... probe8 is bit 7 of byte 0, probe9 is bit 0 of byte 1, and so on.

VALIDATION
    This layout was verified against a capture whose VCD export was already
    parsed independently: all 16 per-channel transition counts matched exactly.
    That check is described in docs/methodology.md. It is a strong check because
    it validates the bit-packing order, not merely the sample count.

SAMPLE RATE
    Read from the metadata "samplerate" key when present. Otherwise pass
    --timescale-ns explicitly. The published analyses all use 10 ns per sample.

USAGE
    python3 sr_to_arrays.py CAPTURE.sr OUTDIR [--timescale-ns 10]
                            [--rename OLD=NEW,...]

    --rename  supplies channel-name corrections at LOAD TIME, so that a capture
              whose embedded metadata mislabels a channel can still be analysed
              correctly. This is the mechanism by which the CH7=DACK correction
              is applied WITHOUT modifying any original capture file.

              Example for the historical floppy captures, whose metadata says
              PMCYC but which were physically DACK:
                  --rename PMCYC=DACK

OUTPUT
    OUTDIR/tr.npz with ts_<NAME> / vs_<NAME>, and OUTDIR/parse_report.txt.

NOTE ON ORIGINALS
    This script opens captures read-only and never writes to them.
"""
import argparse
import os
import sys
import zipfile

import numpy as np


def read_metadata(z):
    md = {}
    if 'metadata' in z.namelist():
        for line in z.read('metadata').decode('utf-8', 'replace').splitlines():
            line = line.strip()
            if '=' in line:
                k, v = line.split('=', 1)
                md[k.strip()] = v.strip()
    return md


def probe_order(md, nchan):
    names = []
    i = 1
    while ('probe%d' % i) in md:
        names.append(md['probe%d' % i])
        i += 1
    if len(names) != nchan:
        names = ['CH%d' % i for i in range(1, nchan + 1)]
    return names


def load(sr_path, renames):
    z = zipfile.ZipFile(sr_path)
    md = read_metadata(z)
    logic = [m for m in z.namelist() if m.startswith('logic-1-')]
    if not logic:
        raise SystemExit('no logic-1-* member: not a 16-or-fewer channel .sr')
    logic.sort(key=lambda s: int(s.rsplit('-', 1)[1]))
    raw = b''.join(z.read(m) for m in logic)
    # 16 channels -> 2 bytes per sample. Derive width from total probes.
    total = int(md.get('total probes', '16'))
    width = max(1, (total + 7) // 8)
    nsamp = len(raw) // width
    arr = np.frombuffer(raw[:nsamp * width], dtype=np.uint8)
    arr = arr.reshape(nsamp, width)
    names = probe_order(md, total)
    out = {}
    for i, nm in enumerate(names):
        byte = i // 8
        bit = i % 8
        col = ((arr[:, byte] >> bit) & 1).astype(np.int8)
        idx = np.flatnonzero(np.concatenate(([True], col[1:] != col[:-1])))
        out[renames.get(nm, nm)] = (idx.astype(np.int64), col[idx])
    return out, md, names, nsamp


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('capture')
    ap.add_argument('outdir')
    ap.add_argument('--timescale-ns', type=float, default=None)
    ap.add_argument('--rename', default='',
                    help='comma-separated OLD=NEW channel renames applied at '
                         'load time, e.g. PMCYC=DACK')
    args = ap.parse_args(argv)

    renames = {}
    for item in args.rename.split(','):
        if '=' in item:
            k, v = item.split('=', 1)
            renames[k.strip()] = v.strip()

    data, md, orig_names, nsamp = load(args.capture, renames)
    os.makedirs(args.outdir, exist_ok=True)
    payload = {}
    for nm, (idx, lv) in data.items():
        payload['ts_' + nm] = idx
        payload['vs_' + nm] = lv
    np.savez_compressed(os.path.join(args.outdir, 'tr.npz'), **payload)

    lines = ['capture: %s' % args.capture,
             'samples: %d' % nsamp,
             'samplerate from metadata: %s' % md.get('samplerate', 'unknown'),
             'probes in file: %s' % ','.join(orig_names),
             'renames applied: %s' % (renames or 'none'),
             '',
             '%-8s %14s  %s' % ('CHANNEL', 'TRANSITIONS', 'LEVELS')]
    for nm in sorted(data):
        idx, lv = data[nm]
        lines.append('%-8s %14d  %s'
                     % (nm, max(0, len(idx) - 1), sorted(set(int(x) for x in lv))))
    open(os.path.join(args.outdir, 'parse_report.txt'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())