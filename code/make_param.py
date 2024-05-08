"""
Make a param file, generating the full set of undirected edges
for a given number of bits (also called dimension)
"""

import sys
import json

nb_bits = int(sys.argv[1])
nb_peaks = int(sys.argv[2])
nb_rse_faces = int(sys.argv[3])

edges = []
sameLevel = {}
for i in range(0, pow(2, nb_bits)):
    iStr = format(i, 'b').zfill(nb_bits)
    for j in range(0, pow(2, nb_bits)):
        jStr = format(j, 'b').zfill(nb_bits)
        n = sum([1 for k in range(nb_bits) if iStr[k] != jStr[k]])
        if n == 1 and i < j:
            edges.append([i, j])
    lvl = sum([1 for k in range(nb_bits) if iStr[k] == "1"])
    if lvl not in sameLevel:
        sameLevel[lvl] = []
    sameLevel[lvl].append(i)

with open(f"data/{nb_bits:02}-{nb_peaks:02}-{nb_rse_faces:02}.json", "w", encoding="utf8") as f:
    json.dump({"nb_bits": nb_bits, "nb_peaks": nb_peaks,
              "nb_rse_faces": nb_rse_faces, "edges": edges}, f, indent=2)
