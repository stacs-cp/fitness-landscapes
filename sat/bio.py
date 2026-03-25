"""
Script for  enumerating or checking existence of various fitness landscapes with different counts of
- peaks
- RSE structures
- SE structures
"""

import itertools
import argparse

import datetime

from lex import lex_smaller_eq

from pysat.formula import *
from pysat.solvers import Solver
from pysat.card import CardEnc

DEFAULT_CARDINALITY_ENCODING = 7  # selected pysat encoding for cardinality constraints
PROJECTED_SET = set()

def anti(v):
    return tuple((1 - x) for x in v)


def flip_i(v, i):
    return tuple((1 - x) if j == i else x for j, x in enumerate(v))


def swap(i, j, v):
    u = list(v)
    u[i], u[j] = u[j], u[i]
    return tuple(u)


def encode(fname, n, partial_sym_break=None, card_type=1, peak_count=None, RSE_count=None, SE_count=None, complete_sym_break=False, complete_sym_break2=False):
    enc = CNF()

    fname.write(f"Card type: {card_type}\n")

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
            
            PROJECTED_SET.add(str(abs(r(u,v))))

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
                enc.append([-t(u, v), -r(v, w), t(u, w)])  # t(u,v) and r(v,w) -> t(u,w)

    # RSE

    if False:
        if RSE_count is not None:
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
        if RSE_count is not None:
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
                    enc.append([-p1, -r(u, v1), r(v2, w)])  # if parallel and r(u,v1) then r(v2,w)
                    enc.append([-p1, -r(v1, u), r(w, v2)])  # if parallel and r(v2,w) then r(u,v1)
                    enc.append([p1, -r(u, v1), r(w, v2)])
                    enc.append([p1, -r(v1, u), r(v2, w)])

                    # variable for saying v1->w is parallel to u->v2
                    p2 = vpool.id()
                    enc.append([-p2, -r(v1, w), r(u, v2)])  # if parallel and r(v1,w) then r(u,v2)
                    enc.append([-p2, -r(w, v1), r(v2, u)])  # if parallel and r(u,v2) then r(v1,w)
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

    if peak_count is not None:
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
        if SE_count is not None:
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
        if SE_count is not None:
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
                    enc.append([-p1, -r(u, v1), r(v2, w)])  # if parallel and r(u,v1) then r(v2,w)
                    enc.append([-p1, -r(v1, u), r(w, v2)])  # if parallel and r(v2,w) then r(u,v1)
                    enc.append([p1, -r(u, v1), r(w, v2)])
                    enc.append([p1, -r(v1, u), r(v2, w)])

                    # variable for saying v1->w is parallel to u->v2
                    p2 = vpool.id()
                    enc.append([-p2, -r(v1, w), r(u, v2)])  # if parallel and r(v1,w) then r(u,v2)
                    enc.append([-p2, -r(w, v1), r(v2, u)])  # if parallel and r(u,v2) then r(v1,w)
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

            if not complete_sym_break and not complete_sym_break2:
                # only consider transpositions of the dimensions
                for i, j in itertools.combinations(range(n), 2):
                    permuted_edges = [(s, (swap(i, j, u), swap(i, j, v))) for s, (u, v) in original_signed_edges]
                    enc = lex_smaller_eq(
                        enc,
                        vpool,
                        [s * r(u, v) for s, (u, v) in original_signed_edges],
                        [s * r(u, v) for s, (u, v) in permuted_edges],
                        maxcomparisons=MAX_COMPARISONS,
                    )
            else:  # complete symmetry breaking
                original_literals = [s * r(u, v) for s, (u, v) in original_signed_edges]
                use_flips = complete_sym_break2

                for P in itertools.permutations(range(n)):
                    flip_masks = itertools.product([0, 1], repeat=n) if use_flips else [(0,) * n]
                    for flip_dimensions in flip_masks:
                        def permute_and_flip(v):
                            return tuple((v[P[i]] if flip_dimensions[i] == 0 else 1 - v[P[i]] for i in range(n)))

                        permuted_edges = [(s, (permute_and_flip(u), permute_and_flip(v))) for s, (u, v) in original_signed_edges]
                        enc = lex_smaller_eq(
                            enc,
                            vpool,
                            [s * r(u, v) for s, (u, v) in permuted_edges],
                            original_literals,
                            
                            maxcomparisons=MAX_COMPARISONS,
                        )

            fname.write(f"number of clauses after adding symmetry breaking: {len(enc.clauses)}\n")

    fname.write(f"Total number of clauses: {len(enc.clauses)}\n")
    fname.write(f"Total number of variables: {vpool.top}\n")
    fname.write(str(PROJECTED_SET)+"\n")
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
    argparser.add_argument("--complete-sym-break", action="store_true", help="Use 'complete' symmetry breaking instead of partial")
    argparser.add_argument("--complete-sym-break2", action="store_true", help="Use 'complete' symmetry breaking including flipping bits")
    argparser.add_argument("--partial-sym-break", type=int, help="Max comparisons for partial symbreak", default=20000)
    argparser.add_argument("--output", "-o", type=str, help="Output path to folder", default="output-"+ datetime.datetime.now().strftime("%Y-%m-%d-%H-%M"))
    
    argparser.add_argument(
        "--cardinality-contraint",
        "--card",
        type=int,
        help="Type of cardinality constraint to use in pysat (1 is sequential)",
        default=DEFAULT_CARDINALITY_ENCODING,
    )
    
    argparser.add_argument(
        "--print-solutions",
        action="store_true",
        help="Prints the solutions to the output"
    )

    args = argparser.parse_args()

    dirname = args.output + "/"
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    if args.SE_count != None:
        filename = dirname + "/dim-" + str(args.n) + "-peak-" + str(args.peak_count) + "-SE-" + str(args.SE_count) + ".txt"
    elif args.RSE_count != None:
        filename = dirname + "/dim-" + str(args.n) + "-peak-" + str(args.peak_count) + "-RSE-" + str(args.RSE_count) + ".txt"
    else:
        filename="default.txt"
    
    f = open(filename, "w")

    f.write(f"Arguments: {args}\n")
    N = args.n

    encoding, var_to_edge = encode(
        f,
        N,
        partial_sym_break=args.partial_sym_break,
        card_type=args.cardinality_contraint,
        peak_count=args.peak_count,
        RSE_count=args.RSE_count,
        SE_count=args.SE_count,
        complete_sym_break=args.complete_sym_break,
        complete_sym_break2=args.complete_sym_break2
    )

#    encoding.to_file(f"norine_switches_pysat_{N}_{args.b}.cnf")
    tmp_file = args.tmp_file

    if args.no_solve:
        encoding.to_file(tmp_file)
        with open(tmp_file, mode="a") as f:
            f.write("c p show " + " ".join(PROJECTED_SET) + " 0\n")
        exit()

    # use pysat solsver
    solver = Solver(name="Cadical195",use_timer=True)
    for clause in encoding:
        solver.add_clause(clause)
    r = True

    num_edge_vars = 2 ** (N - 1) * N

    num_models = 0
    total_model_to_edges_time = 0.0
    total_graph6_write_time = 0.0

    if args.nauty:
        import os
        import time
        from graph6 import graph6
        path_for_graphs = f"graphs_{N}.g6"
        path_for_filtered_graphs = f"graphs_filtered_{N}.g6"

        os.remove(path_for_graphs) if os.path.exists(path_for_graphs) else None
        graph_lines_buffer = []
        graph_buffer_size = 1000
        graph_file = open(path_for_graphs, "a")


    f.write("Start solving...\n")
    while r:
        
        r = solver.solve()
        # f.write("Result:", r, "\n")
        # f.write(f"Time taken: {solver.time():.10f}\n")
        if r:
            num_models += 1
            model = solver.get_model()
            
            if args.print_solutions:
                edges = [var_to_edge[abs(lit)] for lit in model[:num_edge_vars] if lit > 0]
                f.write(edges + "\n")
                
            if args.nauty:
                t0 = time.perf_counter()
                edges = [var_to_edge[abs(lit)] for lit in model[:num_edge_vars] if lit > 0]
                t1 = time.perf_counter()

                t2 = time.perf_counter()
                graph_lines_buffer.append(graph6(edges, N) + "\n")
                if len(graph_lines_buffer) >= graph_buffer_size:
                    graph_file.writelines(graph_lines_buffer)
                    graph_file.flush()
                    graph_lines_buffer.clear()
                t3 = time.perf_counter()

                total_model_to_edges_time += (t1 - t0)
                total_graph6_write_time += (t3 - t2)

                if num_models % 1000 == 0:
                    f.write(
                        f"[timing up to model {num_models}] "
                        f"sum(model->edges)={total_model_to_edges_time:.6f}s "
                        f"sum(graph6+write)={total_graph6_write_time:.6f}s"+ "\n"
                    )

            # solutions.append(red_edges)

            if num_models % 1000 == 0:
                f.write(f"Number of models so far: {num_models}\n")
                f.write(f"Time taken: {solver.time_accum():.10f}\n")

            # block model on edge variables
            solver.add_clause([-model[i] for i in range(num_edge_vars)])
            if not args.all:
                break

    if args.nauty:
        if graph_lines_buffer:
            graph_file.writelines(graph_lines_buffer)
            graph_file.flush()
            graph_lines_buffer.clear()
        graph_file.close()

    if args.all:
        f.write(f"Number of models: {num_models}\n")
        f.write(f"Time taken: {solver.time_accum():.10f}\n")
    else:
        if num_models == 1:
            f.write("SAT\n")
        else:
            f.write("UNSAT\n")
            
    if args.nauty:
        os.system(f"nauty-shortg {path_for_graphs} {path_for_filtered_graphs}")
            
    

