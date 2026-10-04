#!/usr/bin/env python3
"""
clock_c16m.py — measure the C16M clock period by THREE independent methods.

WHY THIS SCRIPT EXISTS
    The single most consequential analysis error in this project's history was
    measuring a square-wave clock by the mean interval between CONSECUTIVE
    transitions. That is the HALF-PERIOD, and it produced a reported frequency
    exactly 2x too high (31.33 MHz for a 15.6671 MHz clock). The error was then
    mistaken for a hardware probe fault.

    This script exists so that cannot happen again by accident. It computes the
    period three ways and refuses to report a number unless they agree.

METHODS
    M1  rising-to-rising   (mean interval between successive 0->1 edges)
    M2  falling-to-falling (mean interval between successive 1->0 edges)
    M3  total_transitions / 2 / duration
        (a square wave has two transitions per cycle)

    All three must agree within --tol MHz or the script exits non-zero.

    EDGE-TO-EDGE IS NOT REPORTED AS A FREQUENCY. It is printed only as an
    explicitly-labelled diagnostic, because it is the quantity that caused the
    original error.

REFERENCE
    Apple, Guide to the Macintosh Family Hardware, 2nd ed., Appendix A:
    C16M = 15.6672 MHz (period ~63.83 ns).

USAGE
    python3 clock_c16m.py ARRAYS_DIR [--tol 0.01]

INPUT
    A directory produced by vcd_to_arrays.py (containing tr.npz).

OUTPUT
    Human-readable report on stdout. Non-zero exit if the three methods
    disagree beyond tolerance.
"""
import os
import sys

import numpy as np

REFERENCE_MHZ = 15.6672


def main(argv):
    if len(argv) < 2:
        sys.stderr.write(__doc__)
        return 2
    d = argv[1]
    tol = 0.01
    if '--tol' in argv:
        tol = float(argv[argv.index('--tol') + 1])

    z = np.load(os.path.join(d, 'tr.npz'))
    if 'ts_C16M' not in z:
        sys.stderr.write('no C16M channel in %s\n' % d)
        return 1
    t, v = z['ts_C16M'], z['vs_C16M']

    rising = t[v == 1]
    falling = t[v == 0]
    if len(rising) < 3 or len(falling) < 3:
        sys.stderr.write('C16M has too few edges (%d/%d)\n'
                         % (len(rising), len(falling)))
        return 1

    # timescale is 10 ns for every VCD in this dataset
    NS = 10.0
    dur_s = (int(t[-1]) - int(t[0])) * NS * 1e-9
    n_edges = len(t) - 1

    p_rise = np.diff(rising)
    p_fall = np.diff(falling)
    m1 = 1000.0 / (p_rise.mean() * NS)
    m2 = 1000.0 / (p_fall.mean() * NS)
    m3 = (n_edges / 2) / dur_s / 1e6
    spread = max(m1, m2, m3) - min(m1, m2, m3)

    print('C16M clock measurement — %s' % d)
    print('  capture window        : %.4f ms' % (dur_s * 1000))
    print('  M1 rising-to-rising   : %d edges, mean %.4f ns -> %.4f MHz'
          % (len(p_rise), p_rise.mean() * NS, m1))
    print('  M2 falling-to-falling : %d edges, mean %.4f ns -> %.4f MHz'
          % (len(p_fall), p_fall.mean() * NS, m2))
    print('  M3 transitions/2/dur  : %d edges          -> %.4f MHz'
          % (n_edges, m3))
    print('  agreement             : spread %.6f MHz (tol %.4f)'
          % (spread, tol))
    print('  REFERENCE [GMFH90] A  : %.4f MHz (period ~63.83 ns)'
          % REFERENCE_MHZ)

    # Diagnostic ONLY. Not a frequency.
    p_edge = np.diff(t)
    print('')
    print('  DIAGNOSTIC (not a frequency): mean edge-to-edge interval')
    print('    %.4f ns  == HALF-PERIOD of %.4f ns'
          % (p_edge.mean() * NS, p_edge.mean() * 2 * NS))
    print('    Reporting this value AS a frequency was the original error.')

    # period histogram: 63.83 ns lands between the 60 and 70 ns sample grid,
    # so it dithers between 6 and 7 units. That dithering is expected.
    vals, counts = np.unique(p_rise, return_counts=True)
    print('')
    print('  rising-period histogram (10 ns units):')
    for v_, c_ in zip(vals, counts):
        print('    %2d units (%3d ns): %d' % (v_, v_ * 10, c_))

    if spread > tol:
        sys.stderr.write('\nFAIL: three methods disagree by %.6f MHz\n' % spread)
        return 1
    dev = abs(m1 - REFERENCE_MHZ)
    print('')
    print('  vs reference: %.4f MHz, deviation %.4f MHz (%.3f%%)'
          % (m1, dev, 100.0 * dev / REFERENCE_MHZ))
    print('  OK: methods agree.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))