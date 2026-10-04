#!/usr/bin/env python3
"""
export_summaries.py — generate the published CSV summaries from array dirs.

Writes:
  data/stock/floppy-read-summary.csv
  data/stock/floppy-write-summary.csv
  data/stock/floppy-read-vs-write.csv

Every row is an OBSERVED MEASUREMENT or DERIVED RESULT. Script paths are
relative so the repository stays portable.
"""
import collections
import csv
import os
import sys

import numpy as np

NS = 10.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(d):
    z = np.load(os.path.join(d, 'tr.npz'))
    return {n[3:]: z[n] for n in z.files if n.startswith('ts_')}, \
           {n[3:]: z[n] for n in z.files if n.startswith('vs_')}


def stats(T, V, d, label):
    a, av = T['AS'], V['AS']
    falls = a[(av == 0) & (np.concatenate(([True], av[:-1] == 1)))]
    rises = a[(av == 1) & (np.concatenate(([False], av[:-1] == 0)))]
    dt, dv = T['DTACK'], V['DTACK']
    da = dt[(dv == 0) & (np.concatenate(([True], dv[:-1] == 1)))]
    dr = dt[(dv == 1) & (np.concatenate(([False], dv[:-1] == 0)))]
    r5 = []
    for n in ('A23', 'A22', 'A21', 'A20', 'A19'):
        i = np.clip(np.searchsorted(T[n], falls, side='right') - 1, 0, len(V[n]) - 1)
        r5.append(V[n][i])
    fl = (r5[0] == 1) & (r5[1] == 1) & (r5[2] == 0) & (r5[3] == 1) & (r5[4] == 1)
    sel = falls[fl]
    rows = []

    def add(metric, sub, value, unit, ev, note=''):
        rows.append([label, metric, sub, value, unit, ev, note])

    add('complete_as_cycles', 'all', len(falls), 'cycles', 'OBSERVED MEASUREMENT')
    add('floppy_window_cycles', 'all', len(sel), 'cycles', 'OBSERVED MEASUREMENT',
        'A23:A19=11011 at /AS')
    for rw, nm in ((1, 'read'), (0, 'write')):
        s = []
        for f in sel:
            i = int(np.searchsorted(T['RW'], int(f), side='right') - 1)
            if int(V['RW'][i]) == rw:
                s.append(int(f))
        add('floppy_cycles', nm, len(s), 'cycles', 'OBSERVED MEASUREMENT')
        if not s:
            continue
        lds0 = collections.Counter(); first = collections.Counter()
        t1 = collections.Counter(); dur = collections.Counter()
        rel = collections.Counter()
        for af in s:
            j = int(np.searchsorted(rises, af, side='left'))
            if j >= len(rises):
                continue
            ar = int(rises[j])
            lds0[int(V['LDS'][int(np.searchsorted(T['LDS'], af, side='right')) - 1])] += 1
            p = int(np.searchsorted(T['LDS'], af, side='left'))
            q = int(np.searchsorted(T['LDS'], ar, side='right'))
            if q > p and int(V['LDS'][p]) == 0:
                first[(int(T['LDS'][p]) - af) * NS] += 1
            k = int(np.searchsorted(da, af, side='left'))
            if k < len(da) and da[k] < ar:
                t1[(int(da[k]) - af) * NS] += 1
                m = int(np.searchsorted(dr, da[k], side='left'))
                if m < len(dr):
                    rel[(int(dr[m]) - ar) * NS] += 1
            dur[(ar - af) * NS] += 1
        add('lds_level_at_as', nm + ';0=active',
            ';'.join('%d=%d' % (k, v) for k, v in sorted(lds0.items())),
            'levels', 'OBSERVED MEASUREMENT')
        add('lds_first_assert_offset', nm,
            ';'.join('%g=%d' % (k, v) for k, v in sorted(first.items())) or 'already_active',
            'ns', 'OBSERVED MEASUREMENT', '+120/+130 are one edge across a sample boundary')
        add('t1_as_to_dtack', nm,
            ';'.join('%g=%d' % (k, v) for k, v in sorted(t1.items())),
            'ns', 'OBSERVED MEASUREMENT')
        add('as_cycle_duration', nm,
            ';'.join('%g=%d' % (k, v) for k, v in sorted(dur.items())),
            'ns', 'OBSERVED MEASUREMENT')
        add('dtack_release_minus_as_rise', nm,
            ';'.join('%g=%d' % (k, v) for k, v in sorted(rel.items())) or 'none',
            'ns', 'OBSERVED MEASUREMENT', 'positive = releases after /AS rises')
    # clock
    t, v = T['C16M'], V['C16M']
    up = t[v == 1]
    per = np.diff(up)
    add('c16m_period_rising_to_rising', 'all', round(per.mean() * NS, 4), 'ns',
        'OBSERVED MEASUREMENT')
    add('c16m_frequency', 'all', round(1000.0 / (per.mean() * NS), 4), 'MHz',
        'OBSERVED MEASUREMENT', 'same-polarity edges; GMFH90 A says 15.6672')
    for n in ('DRQ', 'DACK'):
        if n in T:
            add('%s_transitions' % n.lower(), 'all', len(T[n]) - 1, 'transitions',
                'OBSERVED MEASUREMENT', '0 = static high = deasserted')
    return rows


def main(argv):
    work = argv[1] if len(argv) > 1 else os.path.join(ROOT, 'work')
    outdir = os.path.join(ROOT, 'data', 'stock')
    os.makedirs(outdir, exist_ok=True)
    hdr = ['capture', 'metric', 'population', 'value', 'unit', 'evidence_class', 'note']
    for name, sub in (('floppy-read', 'floppy-read'), ('floppy-write', 'floppy-write')):
        d = os.path.join(work, sub)
        if not os.path.isdir(d):
            sys.stderr.write('missing %s — run scripts/reproduce.sh\n' % d)
            return 1
        T, V = load(d)
        rows = stats(T, V, d, name)
        p = os.path.join(outdir, '%s-summary.csv' % name)
        with open(p, 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(hdr)
            w.writerows(rows)
        print('wrote %s (%d rows)' % (p, len(rows)))
    # comparison
    rows = [
        ['floppy-read-vs-write', 'floppy_cycles', 'read',
         '91500 read / 0 write', 'cycles', 'OBSERVED MEASUREMENT',
         'read capture is write-protected'],
        ['floppy-read-vs-write', 'floppy_cycles', 'write',
         '61716 read / 717 write', 'cycles', 'OBSERVED MEASUREMENT',
         'WARNING: write capture is 98.85% READS'],
        ['floppy-read-vs-write', 'lds_active_at_as', 'read', '100.00', 'percent',
         'OBSERVED MEASUREMENT', '/LDS low at /AS on 91500 of 91500'],
        ['floppy-read-vs-write', 'lds_active_at_as', 'write', '0.00', 'percent',
         'OBSERVED MEASUREMENT', '/LDS high at /AS on all 717 writes'],
        ['floppy-read-vs-write', 'lds_first_assert_offset', 'read', '0', 'ns',
         'OBSERVED MEASUREMENT', 'or already active'],
        ['floppy-read-vs-write', 'lds_first_assert_offset', 'write', '120;130', 'ns',
         'OBSERVED MEASUREMENT', 'one edge quantised either side of a boundary'],
        ['floppy-read-vs-write', 'separation', 'read_vs_write', '100', 'percent',
         'OBSERVED MEASUREMENT', 'zero overlap'],
        ['floppy-read-vs-write', 't1_dominant', 'both', '90;100', 'ns',
         'OBSERVED MEASUREMENT', 'no long-ack class on floppy'],
        ['floppy-read-vs-write', 't1_extra_write_only', 'write', '110', 'ns',
         'OBSERVED MEASUREMENT', '10 of 717 write cycles (1.39%)'],
        ['floppy-read-vs-write', 'dtack_release_after_as_rise', 'both', '100;110', 'ns',
         'OBSERVED MEASUREMENT', 'never negative; identical read and write'],
        ['floppy-read-vs-write', 'rw_setup_dominant', 'write', '-10', 'ns',
         'OBSERVED MEASUREMENT', '661 of 717 write cycles'],
        ['floppy-read-vs-write', 'address_setup_dominant', 'both', '-50', 'ns',
         'OBSERVED MEASUREMENT', 'A3/A4/A5, zero in-cycle address changes'],
        ['floppy-read-vs-write', 'dack_transitions', 'both', '0', 'transitions',
         'OBSERVED MEASUREMENT', 'static high in both directions; stock comparator'],
        ['floppy-read-vs-write', 'mechanism_of_lds_phase_shift', 'n/a',
         'UNRESOLVED', 'n/a', 'UNRESOLVED',
         'A0 and D0-D15 not probed; strobe phase is the measurement, not a cause'],
    ]
    p = os.path.join(outdir, 'floppy-read-vs-write.csv')
    with open(p, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(hdr)
        w.writerows(rows)
    print('wrote %s (%d rows)' % (p, len(rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))