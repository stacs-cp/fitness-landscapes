
# this is how I run it.

python3 data/gen-params-for-peaks-to-table.py

conjure modelling -ac models/fl.essence

function one {
    paramname=$(basename -- "$1")
    paramname="${paramname%.*}"
    if [ -e conjure-output/model000001-$paramname.stats.json ]; then
        echo "Skipping, conjure-output/model000001-$paramname.stats.json exists"
    else
        echo "Running, conjure-output/model000001-$paramname.stats.json doesn't exist"
        conjure solve \
            models/fl.essence $1 \
            --savilerow-options=-O0 \
            --solver=or-tools \
            --solver-options='--threads=8' \
            --output-format=json
    fi
}

export -f one

parallel --no-notice \
    --eta \
    --memfree 100G \
    --joblog gnuparallel-joblog.tsv \
    --results gnuparallel-results \
    one \
    ::: data/peaks-to*param

