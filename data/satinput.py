
face_counts = {3: range(0,6+1), 4: range(0,24+1), 5: range(0,80+1)}

filename = f"satcommands"
with open(filename, "w", encoding="utf8") as f:
    for dimension in [3,4,5]:
        for nb_peaks in range(1,pow(2,dimension-1)):
            for prop in ["RSE"]:
                for edim in [1]:
                    for peak_count in face_counts[dimension]:
                        print(f"""srun --partition sturm --cpus-per-task 2 --mem 16G --time=02:00:00 --chdir $(pwd)/fitness-landscapes --pty bash python sat/bio.py -n {dimension} --partial-sym-break 0 --peak-count {nb_peaks} --RSE-count {peak_count} -a > satoutput/dim-{dimension}-peak-{nb_peaks}-RSE-{peak_count}.txt""", file=f)