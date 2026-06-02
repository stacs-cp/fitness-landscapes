"""
    Transform coloring of hypercube to unique unlabeled graph in graph6 format (for more than 3 dimensions).
"""

import itertools

def flip_i(v, i):
    return tuple((1 - x) if j == i else x for j, x in enumerate(v))

def graph6(red_edges, n):
    import networkx as nx

    g = nx.Graph()

    vertices = list(itertools.product([0, 1], repeat=n))
    g.add_nodes_from(vertices)

        
    m = {u:[0 for _ in range(n)] for u in vertices}
    for u,v in red_edges:
        assert u < v
        
        # get index where different
        diff_idx = next(i for i, (a, b) in enumerate(zip(u, v)) if a != b)
        m[u][diff_idx] = 1

    c = 0
    for u in vertices:
        for i in range(n):
            if u[i] == 1:
                continue # flipping it makes it smaller
            v = flip_i(u, i)

            # Orientation rule: red_edges stores only pairs (u, v) with u < v.
            # If present, use u -> v; otherwise use v -> u.
            src, dst = (u, v) if m[u][i] else (v,u)

            # Directed-edge gadget:
            # src - a - b - dst and marker d attached to a (source side).
            a = f"e{c}_a"
            b = f"e{c}_b"
            d = f"e{c}_d"
            g.add_edge(src, a)
            g.add_edge(a, b)
            g.add_edge(b, dst)
            g.add_edge(a, d)
            c += 1

    return nx.to_graph6_bytes(g, header=False).decode("utf-8").strip()
