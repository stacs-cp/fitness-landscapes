
import json

face_counts = {3: range(0, 6+1),
               4: range(0, 24+1),
               5: range(0, 80+1)}


def doOne(dimension_, nb_peaks_, peak_count_,prop_):
    filename = f"results-2026-05-25-13-00/model000001-peaks-to-{prop_}-"
    filename += f"dimension-{dimension_}-"
    filename += f"peaks-{nb_peaks_}-"
    filename += f"count-{peak_count_}.stats.json"
    # print(filename)
    try:
        with open(filename, "r", encoding="utf8") as f:
            raw = json.load(f)
            if raw["status"] == "OK":
                return raw["savilerowInfo"]["SolverSolutionsFound"]
            else:
                print("STATUS not ok", filename)
                return ""
    except FileNotFoundError:
        print("MISSING", filename)
        return ""


for dimension in [3, 4, 5]:
    for prop in ["RSE", "SE"]:
        outfile = f"dimension-{dimension}-{prop}.csv"
        with open(outfile, "w", encoding="utf8") as out:
            print("Faces/Peaks,"+",".join([str(nb_peaks) for nb_peaks in range(0, 2**(dimension-1)+1)]), file=out)
            for peak_count in face_counts[dimension]:
                print(peak_count, end=",", file=out)
                print(",".join([doOne(dimension, nb_peaks, peak_count,prop) for nb_peaks in range(0, 2**(dimension-1)+1)]), file=out)
