
[ -d pyenv ] || python3 -m venv pyenv
source pyenv/bin/activate
pip install -qr code/requirements.txt



mkdir -p data

parallel --no-notice -j1 python3 code/make_param.py \
    ::: 3 \
    ::: $(seq 0 4) \
    ::: $(seq 0 6)

parallel --no-notice -j1 python3 code/make_param.py \
    ::: 4 \
    ::: $(seq 0 8) \
    ::: $(seq 0 24) \

rm -f conjure-output/*.solution*

function one {
    if [[ $1 == *"solutions.json" ]] || [[ $1 == *"stats.json" ]] ; then
        echo "Skipping $1"
    else
        conjure solve models/fitness.essence $2.json --output-format=json --number-of-solutions=all --solutions-in-one-file
        mv conjure-output/model000001-$3.solutions.json $2.solutions.json
        mv conjure-output/model000001-$3.stats.json $2.stats.json
        python3 code/plot.py $2.solutions.json $2
        rm -f $2
    fi
}

export -f one;

parallel --no-notice -j1 \
    one {} {.} {/.} \
    ::: data/*.json



deactivate
