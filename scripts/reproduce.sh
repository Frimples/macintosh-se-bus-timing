#!/usr/bin/env bash
# reproduce.sh — end-to-end reproduction of the published stock numbers
# from the ORIGINAL .sr captures in this repository.
#
# No sigrok installation is required: sr_to_arrays.py reads the sigrok .sr
# container directly. See scripts/README.md for why.
#
# Usage:  bash reproduce.sh
# Writes intermediate arrays to ./work/ (gitignored).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
WORK="$ROOT/work"
mkdir -p "$WORK"

echo "=== 1. floppy READ -> arrays (CH7 metadata says PMCYC; physically DACK) ==="
python3 "$HERE/sr_to_arrays.py" \
  "$ROOT/captures/stock/floppy-read/stock-se-floppy-read-16ch-a5a3-drq-100mhz-50m.sr" \
  "$WORK/floppy-read" --timescale-ns 10 --rename PMCYC=DACK

echo
echo "=== 2. floppy WRITE -> arrays (same CH7 correction) ==="
python3 "$HERE/sr_to_arrays.py" \
  "$ROOT/captures/stock/floppy-write/stock-se-floppy-write-16ch-a5a3-drq-100mhz-50m.sr" \
  "$WORK/floppy-write" --timescale-ns 10 --rename PMCYC=DACK

echo
echo "=== 3. C16M, three independent methods, both captures ==="
python3 "$HERE/clock_c16m.py" "$WORK/floppy-read"
echo
python3 "$HERE/clock_c16m.py" "$WORK/floppy-write"

echo
echo "=== 4. PRIMARY RESULT: floppy read/write /LDS discriminator ==="
python3 "$HERE/floppy_rw_discriminator.py" "$WORK/floppy-read" "$WORK/floppy-write"

echo
echo "Reproduction complete. Expected headline values:"
echo "  C16M                15.6671 MHz  (period 63.83 ns)"
echo "  floppy READ cycles  91500"
echo "  floppy WRITE cycles 62433 (717 writes = 1.15%, rest are reads)"
echo "  /LDS active at /AS  100% of reads, 0% of writes"