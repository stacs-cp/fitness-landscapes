# Description

`bio.py` is a script to check landscapes with a SAT encoding using symmetry breaking.
To use it, first install pysat.

Example usage
```
python sat/bio.py -n 4 --partial-sym-break 200 --peak-count 5 --SE-count 12 -a
```

- `-n` gives the dimensions
- we can specify the exact counts usin `--peak-count`, `--RSE-count`, and `--SE-count`
- `-a` for enumerating all models
- For deactivating symmetry breaking set `--partial-sym-break 0`
- `--card` for setting a different cardinality in pysat (see pysat documentation)
- For other options use `-h`
