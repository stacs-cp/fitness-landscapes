
import json
import os

face_counts = {3: range(0, 6+1),
               4: range(0, 24+1),
               5: range(0, 80+1)}


def doOne(dimension_, nb_peaks_, peak_count_, prop_):
    filename = f"dim-{dimension_}-peak-{nb_peaks_}-{prop_}-{peak_count_}.txt"
    try:
        remove_file = False
        line_num = 0
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line_num += 1
                line = line.strip()
                if line.startswith("Number of models:"):
                    remove_file = False
                if line.startswith("Number of models so far:"):
                    remove_file = True
            if line_num == 0 or remove_file:
                os.remove(filename)
            
    except Exception as e:
        print(f"Error reading {filename}: {e}")



for dimension in [3, 4, 5]:
    for prop in ["SE","RSE"]:
        for peak_count in face_counts[dimension]:
            for nb_peaks in range(1, 2**(dimension-1)+1):
                doOne(dimension, nb_peaks, peak_count,prop)
