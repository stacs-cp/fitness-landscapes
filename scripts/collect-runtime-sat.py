
import json

face_counts = {3: range(0, 6+1),
               4: range(0, 24+1),
               5: range(0, 80+1)}#, 6: range(0, 240+1)}

def doOne(dimension_, nb_peaks_, peak_count_, face_type_):
    filename = f"output/raw/count-sat-cadical/dim-{dimension_}-peak-{nb_peaks_}-{face_type_}-{peak_count_}.txt"
    try:
        output = "INITIALISED"
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith("Time taken:"):
                    output = line.split("Time taken:")[-1].strip()
            return output
    except Exception as e:
        print(f"Error reading {filename}: {e}")



for dimension in [3, 4, 5]:#, 6]:
    for face_type in ["RSE", "SE"]:
        outfile = f"output/summary/runtimes/count-sat-cadical/dim-{dimension}-{face_type}-time.csv"
        with open(outfile, "w", encoding="utf8") as out:
            print("Faces/Peaks,"+",".join([str(nb_peaks) for nb_peaks in range(1, 2**(dimension-1)+1)]), file=out)
            for peak_count in face_counts[dimension]:
                print(peak_count, end=",", file=out)
                print(",".join([str(doOne(dimension, nb_peaks, peak_count,face_type)) for nb_peaks in range(1, 2**(dimension-1)+1)]), file=out)
