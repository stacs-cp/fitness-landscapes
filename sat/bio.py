"""
Script for checking various conjectures related to Norine's conjecture and improving asymptotic bounds.
"""

import itertools
import argparse
import random

from lex import lex_smaller_eq, checkLexMin

from pysat.formula import *
from pysat.solvers import Solver
from pysat.card import CardEnc


DEFAULT_CARDINALITY_ENCODING = 7  # selected pysat encoding for cardinality constraints


def anti(v):
    return tuple((1 - x) for x in v)


def flip_i(v, i):
    return tuple((1 - x) if j == i else x for j, x in enumerate(v))


def swap(i, j, v):
    u = list(v)
    u[i], u[j] = u[j], u[i]
    return tuple(u)


def encode(n, partial_sym_break=None, card_type=1, peak_count=None, RSE_count=None, SE_count=None):
    enc = CNF()

    print(f"Card type: {card_type}")

    vpool = IDPool(start_from=1)
    vertices = list(itertools.product([0, 1], repeat=n))
    vertices = [v[::-1] for v in vertices]  # reverse to match the order with SMS TODO
    graph = {}
    for v in vertices:
        graph[v] = []
        for i in range(n):
            neighbor = [v[j] if i != j else (1 - v[j]) for j in range(n)]
            graph[v].append(tuple(neighbor))

    for v in vertices:
        assert len(graph[v]) == n, f"Graph is not a hypercube: {v} has {len(graph[v])} neighbors"

    # TODO maybe rename
    def r(u, v):
        # directed edges u->v is present
        if u < v:
            return vpool.id(f"r_{u, v}")
        else:
            return -vpool.id(f"r_{v, u}")

    var_to_edge = dict()

    # add clauses to ensure that the variables are created and the first (important for enumeration)
    for u in vertices:
        for v in graph[u]:
            var_to_edge[r(u, v)] = (u, v)
            enc.append([r(u, v), -r(u, v)])

            if u < v:
                assert sum(u) < sum(v)
            else:
                assert sum(u) > sum(v)

    # 1. transitive closure of directed eges
    def t(u, v):
        # transitive closure of the directed edges
        return vpool.id(f"t_{u, v}")

    # 1.1. forbidding cycles
    for u in vertices:
        for v in graph[u]:
            if u < v:
                enc.append([-t(u, v), -t(v, u)])  # not both t(u,v) and t(v,u)

    # 1.2. base case
    for u in vertices:
        for v in graph[u]:
            enc.append([-r(u, v), t(u, v)])  # r(u,v) -> t(u,v)

    # 1.3. transitivity
    for u, v in itertools.permutations(vertices, 2):
        for w in graph[v]:
            if w != u:
                enc.append([-t(u, v), -r(v, w), t(u, w)])  # t(u,v) and t(v,w) -> t(u,w)

    # RSE

    # SE counts (3-path + last in other direction)
    
    if False:
        if RSE_count:
            RSE_variables = []

            for u in vertices:
                for v1, v2 in itertools.combinations(graph[u], 2):
                    # double w should be the unique neighbor of v1 and v2 other then u
                    w = ((set(graph[v1]) & set(graph[v2])) - {u}).pop()

                    if u > w:
                        continue

                    x = vpool.id()
                    # variables true iff the structure is an RSE

                    enc.append([-x, r(u, v1)])
                    enc.append([-x, r(u, v2)])
                    enc.append([-x, r(w, v1)])
                    enc.append([-x, r(w, v2)])
                    enc.append([x, -r(u, v1), -r(u, v2), -r(w, v1), -r(w, v2)])  # x -> r(u,v1) and r(u,v2) and r(w,v1) and r(w,v2)

                    RSE_variables.append(x)
                    
            enc.extend(
                CardEnc.equals(
                    RSE_variables,
                    bound=RSE_count,
                    vpool=vpool,
                    encoding=card_type,
                )
            )
    else:
        if RSE_count:
            RSE_variables = []

            for u in vertices:
                for v1, v2 in itertools.combinations(graph[u], 2):
                    # double w should be the unique neighbor of v1 and v2 other then u
                    w = ((set(graph[v1]) & set(graph[v2])) - {u}).pop()

                    if u > w:
                        continue
                    if u > v1 or u > v2:
                        continue


                    x = vpool.id()
                    # variables true iff the structure is an SE

                    # variable for saying u -> v1 is parallel to v2 -> w
                    p1 = vpool.id()
                    enc.append([-p1, -r(u, v1), r(v2, w)]) # if parallel and r(u,v1) then r(v2,w)
                    enc.append([-p1, -r(v1, u), r(w, v2)]) # if parallel and r(v2,w) then r(u,v1)
                    enc.append([p1, -r(u, v1), r(w, v2)])
                    enc.append([p1, -r(v1, u), r(v2, w)])

                    # variable for saying v1->w is parallel to u->v2
                    p2 = vpool.id()
                    enc.append([-p2, -r(v1, w), r(u, v2)]) # if parallel and r(v1,w) then r(u,v2)
                    enc.append([-p2, -r(w, v1), r(v2, u)]) # if parallel and r(u,v2) then r(v1,w)
                    enc.append([p2, -r(v1, w), r(v2, u)])
                    enc.append([p2, -r(w, v1), r(u, v2)])

                    # x is (p1 xor p2)

                    enc.append([-x, -p1])
                    enc.append([-x, -p2])
                    enc.append([x, p1, p2])
                    RSE_variables.append(x)
                    
            enc.extend(
                CardEnc.equals(
                    RSE_variables,
                    bound=RSE_count,
                    vpool=vpool,
                    encoding=card_type,
                )
            )

    if peak_count:
        # peaks (all incomming edges)
        peak_variables = []
        for v in vertices:
            x = vpool.id()
            peak_variables.append(x)
            for u in graph[v]:
                enc.append([-x, r(u, v)])  # if peak then incomming edge
            enc.append([x] + [-r(u, v) for u in graph[v]])  # if for all u in N(v) not r(u,v) then x

        enc.extend(
            CardEnc.equals(
                peak_variables,
                bound=peak_count,
                vpool=vpool,
                encoding=card_type,
            )
        )

    if False:
        if SE_count:
            SE_variables = []
            for u in vertices:
                for v1, v2 in itertools.permutations(graph[u], 2):
                    # double w should be the unique neighbor of v1 and v2 other then u
                    w = ((set(graph[v1]) & set(graph[v2])) - {u}).pop()

                    x = vpool.id()
                    # variables true iff the structure is an SE

                    enc.append([-x, r(u, v1)])
                    enc.append([-x, r(v1, w)])
                    enc.append([-x, r(w, v2)])
                    enc.append([-x, -r(v2, u)])
                    enc.append([x, -r(u, v1), -r(v1, w), -r(w, v2), r(v2, u)])

                    SE_variables.append(x)

            

            enc.extend(
                CardEnc.equals(
                    SE_variables,
                    bound=SE_count,
                    vpool=vpool,
                    encoding=card_type,
                )
            )

    # SE version 2
    else:
        if SE_count:
            SE_variables = []
            for u in vertices:
                for v1, v2 in itertools.combinations(graph[u], 2):
                    # double w should be the unique neighbor of v1 and v2 other then u
                    w = ((set(graph[v1]) & set(graph[v2])) - {u}).pop()

                    if u > w:
                        continue
                    if u > v1 or u > v2:
                        continue


                    x = vpool.id()
                    # variables true iff the structure is an SE

                    # variable for saying u -> v1 is parallel to v2 -> w
                    p1 = vpool.id()
                    enc.append([-p1, -r(u, v1), r(v2, w)]) # if parallel and r(u,v1) then r(v2,w)
                    enc.append([-p1, -r(v1, u), r(w, v2)]) # if parallel and r(v2,w) then r(u,v1)
                    enc.append([p1, -r(u, v1), r(w, v2)])
                    enc.append([p1, -r(v1, u), r(v2, w)])

                    # variable for saying v1->w is parallel to u->v2
                    p2 = vpool.id()
                    enc.append([-p2, -r(v1, w), r(u, v2)]) # if parallel and r(v1,w) then r(u,v2)
                    enc.append([-p2, -r(w, v1), r(v2, u)]) # if parallel and r(u,v2) then r(v1,w)
                    enc.append([p2, -r(v1, w), r(v2, u)])
                    enc.append([p2, -r(w, v1), r(u, v2)])

                    # x is (p1 xor p2)

                    enc.append([-x, -p1, -p2])
                    enc.append([-x, p1, p2])
                    enc.append([x, -p1, p2])
                    enc.append([x, p1, -p2])
                    SE_variables.append(x)

            enc.extend(
                CardEnc.equals(
                    SE_variables,
                    bound=SE_count,
                    vpool=vpool,
                    encoding=card_type,
                )
            )

    

    # Symmetry breaking

    v = vertices[0]
    for u in graph[v]:
        enc.append([r(v, u)])  # fix one outgoing edge from the first vertex

    if True:
        if partial_sym_break:
            MAX_COMPARISONS = partial_sym_break

            # cls_pre_sb = enc.n_clauses()
            original_signed_edges = [(1, (u, v)) for u in vertices for v in graph[u] if u < v]

            for i, j in itertools.combinations(range(n), 2):
                permuted_edges = [(s, (swap(i, j, u), swap(i, j, v))) for s, (u, v) in original_signed_edges]
                enc = lex_smaller_eq(
                    enc,
                    vpool,
                    [s * r(u, v) for s, (u, v) in original_signed_edges],
                    [s * r(u, v) for s, (u, v) in permuted_edges],
                    maxcomparisons=MAX_COMPARISONS,
                )

            if True:  # complete symmetry breaking
                for P in itertools.permutations(range(n)):
                    flip_dimensions = [0 for _ in range(n)]  # TODO no flips for now

                    def permute_and_flip(v):
                        # print(f"Permuting {v} with {P} and flipping {flip_dimensions}")
                        return tuple((v[P[i]] if flip_dimensions[i] == 0 else 1 - v[P[i]] for i in range(n)))

                    permuted_edges = [(s, (permute_and_flip(u), permute_and_flip(v))) for s, (u, v) in original_signed_edges]
                    enc = lex_smaller_eq(
                        enc,
                        vpool,
                        [s * r(u, v) for s, (u, v) in original_signed_edges],
                        [s * r(u, v) for s, (u, v) in permuted_edges],
                        maxcomparisons=MAX_COMPARISONS,
                    )

            print(f"number of clauses after adding symmetry breaking: {len(enc.clauses)}")

    print(f"Total number of clauses: {len(enc.clauses)}")

    return enc, var_to_edge


import os

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Norine's conjecture")
    argparser.add_argument("-n", type=int, help="Order of the hypercube graph", required=True)
    argparser.add_argument("--peak-count", type=int, help="Exact number of peaks of the landscape")
    argparser.add_argument("--RSE-count", type=int, help="Exact number of RSE structures")
    argparser.add_argument("--SE-count", type=int, help="Exact number of SE structures")
    argparser.add_argument("--tmp-file", type=str, help="Temporary file to store the encoding", default="norine_tmp.cnf")
    argparser.add_argument("--no-solve", action="store_true", help="Do not use solver, just create the encoding and save it to the temp file")
    argparser.add_argument(
        "--nauty", action="store_true", help="Use nauty for checking final solutions for isomorphic copies(only if pysat solver is used)"
    )
    argparser.add_argument(
        "--use-pysat-solver", action="store_true", help="Use pysat solver instead of custom SMS version and check for isomorphic copies at the end"
    )
    argparser.add_argument("-a", "--all", action="store_true", help="Enumerate all models")
    argparser.add_argument("--partial-sym-break", type=int, help="Max comparisons for partial symbreak", default=20000)

    argparser.add_argument(
        "--cardinality-contraint",
        "--card",
        type=int,
        help="Type of cardinality constraint to use in pysat (1 is sequential)",
        default=DEFAULT_CARDINALITY_ENCODING,
    )

    args = argparser.parse_args()

    print(f"Arguments: {args}")
    N = args.n

    encoding, var_to_edge = encode(
        N,
        partial_sym_break=args.partial_sym_break,
        card_type=args.cardinality_contraint,
        peak_count=args.peak_count,
        RSE_count=args.RSE_count,
        SE_count=args.SE_count,
    )

    # encoding.to_file(f"norine_switches_pysat_{N}_{args.b}.cnf")
    tmp_file = args.tmp_file

    if args.no_solve:
        encoding.to_file(tmp_file)
        exit()

    # use pysat solsver
    solver = Solver(name="Cadical195")
    for clause in encoding:
        solver.add_clause(clause)
    r = True

    num_edge_vars = 2 ** (N - 1) * N

    num_models = 0
    num_minimal_models = 0

    solutions = []

    path_for_graphs = f"graphs_{N}.g6"
    path_for_filtered_graphs = f"graphs_filtered_{N}.g6"

    os.remove(path_for_graphs) if os.path.exists(path_for_graphs) else None

    print("Start solving...")
    while r:
        r = solver.solve()
        # print("Result:", r)

        if r:
            num_models += 1
            model = solver.get_model()
            # red_edges = [var_to_edge[abs(lit)] for lit in model[:num_edge_vars] if lit > 0]

            # solutions.append(red_edges)

            if num_models % 1000 == 0:
                print(f"Number of models so far: {num_models}")

            # block model on edge variables
            solver.add_clause([-model[i] for i in range(num_edge_vars)])
            if not args.all:
                break

    if args.all:
        print(f"Number of models: {num_models}")
    else:
        if num_models == 1:
            print("SAT")
        else:
            print("UNSAT")
