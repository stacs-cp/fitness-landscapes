
import json

face_counts = {3: range(6, 6+1),
               4: range(24, 24+1),
               5: range(80, 80+1),
               6: range(240, 240+1),
               7: range(672, 672+1),
               8: range(1792,1792+1)}



def doOne(dimension_, nb_peaks_, peak_count_):
    filename = f"dim-{dimension_}-peak-{nb_peaks_}-SE-{peak_count_}.txt"
    # print(filename)
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith("Number of models:"):
                    output = line.split("Number of models:")[-1].strip()
                    print(output)
                    return output
                    break  # Assuming only one "Number of models" line per file
    except Exception as e:
        print(f"Error reading {filename}: {e}")



# for dimension in [3, 4, 5]:
outfile = "SE-bottom-left-seq.csv"
with open(outfile, "w", encoding="utf8") as out:
    for dimension in [3, 4, 5, 6, 7, 8]:
        print("Faces/Peaks,"+",".join([str(nb_peaks) for nb_peaks in range(1, 1+1)]), file=out)
        for peak_count in face_counts[dimension]:
            print(peak_count, end=",", file=out)
            print(",".join([str(doOne(dimension, nb_peaks, peak_count)) for nb_peaks in range(1, 1+1)]), file=out)
