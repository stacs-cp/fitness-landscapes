
To run: `bash code/run.sh`


## Oz's notes


Listing largest files in a directory: du -s * | sort -n

Compressing the largest X of them (replace X with a number of your choosing): parallel --no-notice --eta gzip -9 ::: $(du -s * | sort -n | tail -nX | cut -f 2)

Extracting number of solution from solutions.json files: parallel --no-notice -j20 --eta --joblog jq-joblog.tsv "jq -r '[input_filename, length] | join(\"\t\")' {} > {#}.bit" ::: conjure-output/model000001-peaks-to-*.solutions.json


