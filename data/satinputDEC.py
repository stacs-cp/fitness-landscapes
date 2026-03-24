import os
import datetime

face_counts = {3: range(0,6+1), 4: range(0,24+1), 5: range(0,80+1)}

filename = f"satcommandsDEC"
outdir = "results-"+ datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
with open(filename, "w", encoding="utf8") as f:
    for dimension in [3,4,5]:
        for nb_peaks in range(1,pow(2,dimension-1)+1):
            for prop in ["RSE","SE"]:
                for peak_count in face_counts[dimension]:
                    #outfile = f"SATresultsDEC/dim-{dimension}-peak-{nb_peaks}-{prop}-{peak_count}.txt"
                    #if not os.path.exists(outfile):
                    print(f"""python sat/bio.py -n {dimension} --partial-sym-break 0 --peak-count {nb_peaks} --{prop}-count {peak_count} --output {outdir}""", file=f)
