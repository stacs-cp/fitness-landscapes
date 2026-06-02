"""
Plotting a solution from a given json solution file.
"""

import sys
import json
import graphviz

with open(sys.argv[1], "r", encoding="utf8") as f:
    solutions = json.load(f)
    d = graphviz.Digraph()
    for solution in solutions:
        g = solution["g"]
        w = solution["w"]
        rse_witnesses = solution["rse_witnesses"]

        for i, iVals in g.items():
            if len(rse_witnesses) > 0 and int(i) in rse_witnesses[0]:
                d.node(f'{i} (w {w[i]})', style='filled', fillcolor='yellow')

        for i, iVals in g.items():
            for j, jVal in iVals.items():
                if jVal:
                    # print(i, j, weights[i], weights[j])
                    d.edge(f'{i} (w {w[i]})', f'{j} (w {w[j]})')

        d.render(f"{sys.argv[2]}", format="pdf")

        # just plot the first solution
        sys.exit(0)
