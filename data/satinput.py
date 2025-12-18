
face_counts = {#3: range(0, 6+1),
               #4: range(0, 24+1),
               6: range(235,240+1)}

filename = f"satcommands"
with open(filename, "w", encoding="utf8") as f:
    for dimension in [6]:
        for nb_peaks in range(1, 2**(dimension-1)+1):
            for prop in ["SE"]:
                for edim in [1]:
                    for peak_count in face_counts[dimension]:
                        print(f"""python sat/bio.py -n {dimension} --partial-sym-break 0 --peak-count {nb_peaks} --SE-count {peak_count} -a > satoutput/dim-{dimension}-peak-{nb_peaks}-SE-{peak_count}.txt""", file=f)
