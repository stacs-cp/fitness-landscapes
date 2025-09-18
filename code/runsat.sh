
# this is how I run it.

python3 data/satinput.py

mkdir satoutput

more satcommands | parallel 
    --no-notice \
    --memfree 100G \
    --eta \
    --joblog gnuparallel-joblog.tsv \
    --results gnuparallel-results