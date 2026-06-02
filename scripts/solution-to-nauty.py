"""
Plotting a solution from a given json solution file.
"""
import json
solutions = json.loads(open('fl-profiling-profiling.solutions.json').read())
print(len(solutions))

dim = 3

import itertools
def bitstr(tpl):
    return ''.join(str(b) for b in tpl)

def median_elements(lst):
    n = len(lst)
    if n == 0:
        return []
    mid = n // 2
    if n % 2 == 1:     # odd length - single middle
        return [lst[mid]]
    else:              # even length - the two central
        return [lst[mid - 1], lst[mid]]

def display_sol(sol):

    nodes = list(itertools.product([0,1], repeat=dim))

    # Build node ids and labels up front
    node_info = {}
    for n in nodes:
        nid = bitstr(n)  # e.g., "010"
        # assuming w is defined globally as w[x][y][z]
        lbl = f'{nid} w({w[n[0]][n[1]][n[2]]})'
        node_info[n] = (nid, lbl)

    # 1) Create nodes
    for n, (nid, lbl) in node_info.items():
        d.node(nid, label=lbl)

    # 2) Layer by Hamming weight and enforce lexicographic order within each layer
    for k in range(dim + 1):
        layer_nodes = [n for n in nodes if sum(n) == k]
        layer_nodes.sort(key=lambda n: bitstr(n))  # "000" < "001" < "010" < ...

        with d.subgraph() as sg:
            sg.attr(rank='same')
            # Add invisible edges to force left-to-right order within the rank
            for i in range(len(layer_nodes) - 1):
                a = node_info[layer_nodes[i]][0]
                b = node_info[layer_nodes[i + 1]][0]
                sg.edge(a, b, style='invis', weight='100')

    # Add invisible edges to force top-down order across ranks
    # This goes from median nodes of a layer to the median nodes of the next layer
    for k1 in range(dim):
        k2 = k1 + 1
        layer_nodes1 = [n for n in nodes if sum(n) == k1]
        layer_nodes1.sort(key=lambda n: bitstr(n))
        layer_nodes2 = [n for n in nodes if sum(n) == k2]
        layer_nodes2.sort(key=lambda n: bitstr(n))
        median_nodes1 = median_elements(layer_nodes1)
        median_nodes2 = median_elements(layer_nodes2)

        for a in median_nodes1:
            for b in median_nodes2:
                a_id = node_info[a][0]
                b_id = node_info[b][0]
                d.edge(a_id, b_id, style='invis', weight='1000')

    # 3) Add the real edges (only between nodes that differ by 1 bit, w1 < w2)
    for n1 in nodes:
        for n2 in nodes:
            if sum(1 for i in range(dim) if n1[i] != n2[i]) == 1:
                w1 = w[n1[0]][n1[1]][n1[2]]
                w2 = w[n2[0]][n2[1]][n2[2]]
                if w1 < w2:
                    d.edge(node_info[n1][0], node_info[n2][0], weight='1')

    # for nb_bits in range(dim+1):
    #     with d.subgraph() as s:
    #         s.attr(rank="same")
    #         for node1 in nodes:
    #             if sum(node1) == nb_bits:
    #                 w1 = w[node1[0]][node1[1]][node1[2]]
    #                 s.node(f'{node1[0]}{node1[1]}{node1[2]} w({w1})')

    # for node1 in nodes:
    #     for node2 in nodes:
    #         w1 = w[node1[0]][node1[1]][node1[2]]
    #         w2 = w[node2[0]][node2[1]][node2[2]]
    #         if w1 < w2 and sum([ 1 for i in range(dim) if node1[i] != node2[i] ]) == 1:
    #             d.edge(f'{node1[0]}{node1[1]}{node1[2]} w({w1})', f'{node2[0]}{node2[1]}{node2[2]} w({w2})')

    display(d)


for (n, sol) in enumerate(solutions):
    w = sol['w']
    print(f'Solution {n+1} -- nb_peaks={sol["nb_peaks"]}, nb_se_faces_with_lex_all={sol["nb_se_faces_with_lex_all"]}, nb_se_faces_with_lex={sol["nb_se_faces_with_lex"]}, nb_se_faces_no_lex={sol["nb_se_faces_no_lex"]}, nb_rse_faces={sol["nb_rse_faces"]}')
    display_sol(w)
