
# this is how I run it.

python3 data/gen-params-for-peaks-to-table.py
#!/bin/sh

rm -f cpcommands

function one {
    paramname=$(basename -- "$1")
    paramname="${paramname%.*}"

    echo conjure solve \
        models/edge.essence $1 \
        --use-existing-models=conjure-output/model000001.eprime \
        --savilerow-options=-O1 \
        --solver=minion \
        --number-of-solutions=all \
        --copy-solutions=no \
    	--solutions-in-one-file \
        --output-format=json >> cpcommands
}

export -f one

parallel --no-notice -j1 one ::: data/peaks-to-*.param

# At this point cpcommands contains all commands we want to run.