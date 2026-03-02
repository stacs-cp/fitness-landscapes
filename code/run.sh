
# this is how I run it.

python3 data/gen-params-for-peaks-to-table.py

conjure modelling -ac models/fl.essence

function one {
    paramname=$(basename -- "$1")
    paramname="${paramname%.*}"
    if [ -e conjure-output/model000001-$paramname.stats.json ]; then
        echo "Skipping, conjure-output/model000001-$paramname.stats.json exists"
    else
        echo "Running, conjure-output/model000001-$paramname.stats.json"
        srun --partition sturm --cpus-per-task 2 --mem 16G --time=02:00:00 --chdir $(pwd)/fitness-landscapes --pty bash conjure solve \
            models/fl.essence $1 \
            --use-existing-models=conjure-output/model000001.eprime \
            --savilerow-options=-O1 \
            --solver=minion \
	    --number-of-solutions=all \
            --copy-solutions=no \
	    --solutions-in-one-file \
            --output-format=json
    fi
	    # --solver-options "-parallel -cores 160" \
}

export -f one

parallel --no-notice \
    --memfree 100G \
    --eta \
    --joblog gnuparallel-joblog.tsv \
    --results gnuparallel-results \
    one \
    ::: data/peaks-to*param

