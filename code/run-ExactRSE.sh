
[ -d pyenv ] || python3 -m venv pyenv
source pyenv/bin/activate
pip install -qr code/requirements.txt



mkdir -p data-ExactRSE

parallel --no-notice python3 code/make_param.py data-ExactRSE \
    ::: 3 \
    ::: $(seq 0 4) \
    ::: $(seq 0 6)

parallel --no-notice python3 code/make_param.py data-ExactRSE \
    ::: 4 \
    ::: $(seq 0 8) \
    ::: $(seq 0 24) \

parallel --no-notice python3 code/make_param.py data-ExactRSE \
    ::: 5 \
    ::: $(seq 0 16) \
    ::: $(seq 0 80) \

rm -f conjure-output/ExactRSE/*.solution*

function one {
    if [[ $1 == *".solutions.json" ]] || [[ $1 == *".stats.json" ]] ; then
        echo "Skipping $1"
    elif [ -f $2.stats.json ]; then
        echo "Skipping $1, stats.json exists already"
    else
        conjure solve models/fitness-ExactRSE.essence $2.json --solver=kissat --output-format=json --number-of-solutions=1 --solutions-in-one-fil -o conjure-output/ExactRSE
        mv conjure-output/ExactRSE/model000001-$3.solutions.json $2.solutions.json
        mv conjure-output/ExactRSE/model000001-$3.stats.json $2.stats.json
        python3 code/plot.py $2.solutions.json $2
        rm -f $2
    fi
}

export -f one;

parallel --no-notice --eta --results gnuparallel-results --joblog gnuparallel-joblog.tsv \
    one {} {.} {/.} \
    ::: data-ExactRSE/*.json

mkdir -p stats
echo "Instance, SR Time, Solver Time, Number of solutions (counting up to 1)" > stats/counts-ExactRSE.csv
jq -j '.essenceParams[0], ", ", .savilerowInfo.SavileRowTotalTime, ", ", .savilerowInfo.SolverTotalTime, ", ", .savilerowInfo.SolverSatisfiable, "\n"' data-ExactRSE/*.stats.json >> stats/counts-ExactRSE.csv


deactivate
