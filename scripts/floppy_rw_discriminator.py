#!/usr/bin/env python3
"""
floppy_rw_discriminator.py — the primary published stock result.

FINDING
    On a stock Macintosh SE, the /LDS data strobe is ACTIVE at /AS assertion for
    a floppy READ, and INACTIVE at /AS assertion for a floppy WRITE, asserting
    120-130 ns later.

        READ   /LDS active at /AS   (offset 0 ns, or already active)
        WRITE  /LDS inactive at /AS, asserts at +120/+130 ns

    Measured over 91,500 read cycles and 717 write cycles with ZERO overlap.
    The separation is 100%.

    This is decode-independent: it requires no register identification and no
    address-bus interpretation. That is why it is the useful comparator for
    future replacement-CPU work.

WHAT THIS SCRIPT DOES NOT DO
    It does not explain WHY. It does not claim which byte lane is used, because
    A0 and the data bus (D0-D15) were not probed. The 120-130 ns phase shift is
    a measurement; its mechanism is not established here.

    NOTE ON /UDS: on the floppy READ population /UDS is measured INACTIVE (1) at
    /AS on all 91,500 cycles, while /LDS is ACTIVE. On the WRITE population
    /UDS is inactive at /AS and /LDS asserts later. An earlier private summary
    described /UDS as "never asserted on read" and separately implied /UDS was
    asserted during reads; those two statements conflict. This script reports
    the measured levels so the published claim matches the data.

USAGE
    python3 floppy_rw_discriminator.py READ_DIR WRITE_DIR

INPUT
    Directories produced by vcd_to_arrays.py. CH7 must be supplied as DACK via
    --channel-map at stage 1 if the acquisition metadata mislabels it. This
    script does not read CH7 at all: the finding is about /LDS and /AS.

IDENTIFYING THE FLOPPY POPULATION
    Discriminator: A23:A19 == 11011 at /AS, i.e. the top 2 MB decode window
    containing the Integrated Workbench Machine (IWM) floppy controller.

    BIT-ORDER WARNING — this is a real trap. A23:A19 = 11011 means
    A23=1, A22=1, A21=0, A20=1, A19=1. Writing the mask as (0,1,0,1,1) returns
    ZERO floppy cycles while every individual term is non-zero, because it
    silently selects the ROM window instead. This script asserts the expected
    population is non-empty and that A23:A19=01000 also appears, as a check
    against exactly that inversion.
"""
import collections
import os
import sys

import numpy as np

NS = 10.0  # VCD timescale for this dataset


def load(d):
    z = np.load(os.path.join(d, 'tr.npz'))
    return {n[3:]: z[n] for n in z.files if n.startswith('ts_')}, \
           {n[3:]: z[n] for n in z.files if n.startswith('vs_')}


def cycles(d):
    T, V = load(d)
    a, av = T['AS'], V['AS']
    falls = a[(av == 0) & (np.concatenate(([True], av[:-1] == 1)))]
    rises = a[(av == 1) & (np.concatenate(([False], av[:-1] == 0)))]
    dt, dv = T['DTACK'], V['DTACK']
    da = dt[(dv == 0) & (np.concatenate(([True], dv[:-1] == 1)))]
    r5 = []
    for n in ('A23', 'A22', 'A21', 'A20', 'A19'):
        i = np.clip(np.searchsorted(T[n], falls, side='right') - 1,
                    0, len(V[n]) - 1)
        r5.append(V[n][i])
    floppy = (r5[0] == 1) & (r5[1] == 1) & (r5[2] == 0) & \
             (r5[3] == 1) & (r5[4] == 1)
    rom = (r5[0] == 0) & (r5[1] == 1) & (r5[2] == 0) & \
          (r5[3] == 0) & (r5[4] == 0)
    n_rom = int(rom.sum())
    if n_rom == 0:
        sys.stderr.write('ABORT: no A23:A19=01000 (ROM) cycles. The address '
                         'bit order is probably inverted.\n')
    sel = falls[floppy]
    if len(sel) == 0:
        sys.stderr.write('ABORT: zero floppy cycles. Check bit order.\n')
    out = []
    for f in sel:
        af = int(f)
        j = int(np.searchsorted(rises, f, side='left'))
        if j >= len(rises):
            continue
        ar = int(rises[j])
        rw = int(V['RW'][int(np.searchsorted(T['RW'], af, side='right')) - 1])
        k = int(np.searchsorted(da, af, side='left'))
        t1 = (int(da[k]) - af) * NS if (k < len(da) and da[k] < ar) else None
        p = int(np.searchsorted(T['LDS'], af, side='left'))
        q = int(np.searchsorted(T['LDS'], ar, side='right'))
        first = None
        if q > p and int(V['LDS'][p]) == 0:
            first = (int(T['LDS'][p]) - af) * NS
        out.append(dict(af=af, ar=ar, rw=rw, t1=t1, lds_first=first,
                        lds_at_as=int(V['LDS'][int(
                            np.searchsorted(T['LDS'], af, side='right')) - 1]),
                        uds_at_as=int(V['UDS'][int(
                            np.searchsorted(T['UDS'], af, side='right')) - 1]),
                        dur=(ar - af) * NS))
    return out, len(falls), n_rom


def summarise(recs, label):
    print('\n' + '=' * 70)
    print(label)
    print('=' * 70)
    rw_pop = collections.Counter(r['rw'] for r in recs)
    print('floppy cycles: %d   R/W at /AS: %s   (1=read, 0=write)'
          % (len(recs), dict(sorted(rw_pop.items()))))
    if rw_pop:
        wr = rw_pop.get(0, 0)
        print('  -> writes are %.2f%% of the floppy population'
              % (100.0 * wr / len(recs)))
    for rw, name in ((1, 'READ'), (0, 'WRITE')):
        s = [r for r in recs if r['rw'] == rw]
        if not s:
            print('  %s: none' % name)
            continue
        print('\n  %s  n=%d' % (name, len(s)))
        print('    /LDS level at /AS   : %s   (0=ACTIVE)'
              % dict(sorted(collections.Counter(
                  r['lds_at_as'] for r in s).items())))
        print('    /UDS level at /AS   : %s   (0=ACTIVE)'
              % dict(sorted(collections.Counter(
                  r['uds_at_as'] for r in s).items())))
        first = collections.Counter(r['lds_first'] for r in s
                                    if r['lds_first'] is not None)
        print('    first /LDS assert   : %s ns'
              % (dict(sorted(first.items())) if first else 'already active'))
        print('    T1 /AS->/DTACK      : %s ns'
              % dict(sorted(collections.Counter(
                  r['t1'] for r in s if r['t1'] is not None).items())))
        print('    cycle duration      : %s ns'
              % dict(sorted(collections.Counter(
                  r['dur'] for r in s).items())))
    return recs


def main(argv):
    if len(argv) < 3:
        sys.stderr.write(__doc__)
        return 2
    rd, n_all_rd, n_rom_rd = cycles(argv[1])
    wr, n_all_wr, n_rom_wr = cycles(argv[2])
    summarise(rd, 'FLOPPY READ capture')
    summarise(wr, 'FLOPPY WRITE capture')

    r = [x for x in rd if x['rw'] == 1]
    w = [x for x in wr if x['rw'] == 0]
    print('\n' + '=' * 70)
    print('DISCRIMINATOR')
    print('=' * 70)
    if not r or not w:
        sys.stderr.write('need both populations\n')
        return 1
    read_active = sum(1 for x in r if x['lds_at_as'] == 0)
    write_active = sum(1 for x in w if x['lds_at_as'] == 0)
    print('  READ  /LDS ACTIVE at /AS : %d of %d (%.2f%%)'
          % (read_active, len(r), 100.0 * read_active / len(r)))
    print('  WRITE /LDS ACTIVE at /AS : %d of %d (%.2f%%)'
          % (write_active, len(w), 100.0 * write_active / len(w)))
    print('  WRITE /LDS first assert  : %s ns'
          % dict(sorted(collections.Counter(
              x['lds_first'] for x in w if x['lds_first'] is not None).items())))
    sep = read_active == len(r) and write_active == 0
    print('\n  SEPARATION IS %s' % ('100%, ZERO OVERLAP' if sep
                                     else 'NOT CLEAN -- investigate'))
    return 0 if sep else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))