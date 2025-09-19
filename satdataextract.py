
import json

face_counts = {3: range(0, 6+1),
               4: range(0, 24+1),
               5: range(0, 80+1)}


def doOne(dimension_, nb_peaks_, peak_count_):
    filename = f"sturmoutput/fitness/satoutput/dim-{dimension_}-peak-{nb_peaks_}-SE-{peak_count_}.txt"
    # print(filename)
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith("Number of models:"):
                    output = line.split("Number of models:")[-1].strip()
                    return output
                    break  # Assuming only one "Number of models" line per file
    except Exception as e:
        print(f"Error reading {filename}: {e}")



# for dimension in [3, 4, 5]:
for dimension in [3, 4, 5]:
    outfile = f"dim-{dimension}-SE.csv"
    with open(outfile, "w", encoding="utf8") as out:
        print("Faces/Peaks,"+",".join([str(nb_peaks) for nb_peaks in range(0, 2**(dimension-1)+1)]), file=out)
        for peak_count in face_counts[dimension]:
            print(peak_count, end=",", file=out)
            print(",".join([str(doOne(dimension, nb_peaks, peak_count)) for nb_peaks in range(0, 2**(dimension-1)+1)]), file=out)
