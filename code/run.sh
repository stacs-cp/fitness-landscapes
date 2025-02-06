
# this is how I run it.

python3 data/gen-params-for-peaks-to-table.py

conjure modelling -ac models/fl.essence

parallel --no-notice \
    --eta \
    --joblog gnuparallel-joblog.tsv \
    --results gnuparallel-results \
    "conjure solve models/fl.essence {} --savilerow-options=-O0 --solver=or-tools --line-width=60" \
    ::: data/peaks-to*param

