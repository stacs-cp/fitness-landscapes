
import json

face_counts = {3: range(0, 6+1),
               4: range(0, 24+1),
               5: range(0, 80+1)}


def doOne(dimension_, edim_, nb_peaks_, peak_count_):
    filename = f"conjure-output/model000001-peaks-to-{prop}-"
    filename += f"dimension{dimension_}-"
    filename += f"edim{edim_}-"
    filename += f"peaks{nb_peaks_}-"
    filename += f"count{peak_count_}.stats.json"
    # print(filename)
    try:
        with open(filename, "r", encoding="utf8") as f:
            raw = json.load(f)
            if raw["status"] == "OK":
                return raw["savilerowInfo"]["SolverSatisfiable"]
            else:
                print("STATUS not ok", filename)
                return ""
    except FileNotFoundError:
        print("MISSING", filename)
        return ""


# for dimension in [3, 4, 5]:
for dimension in [3, 4, 5]:
    for prop in ["RSE", "SE"]:
        for edim in range(1, dimension):
            outfile = f"dimension{dimension}-prop{prop}-edim{edim}.csv"
            with open(outfile, "w", encoding="utf8") as out:
                print("Faces/Peaks,"+",".join([str(nb_peaks)
                      for nb_peaks in range(0, 2**(dimension-1)+1)]), file=out)

                for peak_count in face_counts[dimension]:

                    print(peak_count, end=",", file=out)

                    print(",".join([doOne(dimension, edim, nb_peaks, peak_count)
                                    for nb_peaks in range(0, 2**(dimension-1)+1)]), file=out)
