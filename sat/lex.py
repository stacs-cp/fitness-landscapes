def lex_smaller_eq(enc, vpool, seq1, seq2, maxcomparisons=None):
    """Ensure that seq1 is lexicographically smaller or equal than seq2"""
    assert len(seq1) == len(seq2)
    all_previous_equal = vpool.id()
    enc.append([+all_previous_equal])
    rcnt = 0
    for i in range(len(seq1)):
        if seq1[i] == seq2[i]:
            continue
        rcnt += 1
        enc.append([-all_previous_equal, -seq1[i], +seq2[i]])  # all previous equal implies seq1[i] <= seq2[i]
        all_previous_equal_new = vpool.id()
        enc.append([-all_previous_equal, -seq1[i], +all_previous_equal_new])
        enc.append([-all_previous_equal, +seq2[i], +all_previous_equal_new])
        all_previous_equal = all_previous_equal_new
        if maxcomparisons is not None and rcnt > maxcomparisons:
            break
    return enc


import itertools


def checkLexMin(red_edges, n, plusNegated=False):
    """
    Checks whether minimal
    """

    vertices = list(itertools.product([0, 1], repeat=n))
    graph = {}
    for v in vertices:
        graph[v] = set()
        for i in range(n):
            neighbor = [v[j] if i != j else (1 - v[j]) for j in range(n)]
            graph[v].add(tuple(neighbor))

    original_edges = [(u, v) for u in vertices for v in graph[u] if u < v]

    def edges_to_sequence(red_edges):
        return [1 if (u, v) in red_edges or (v, u) in red_edges else 0 for u, v in original_edges]

    original_edges_seq = edges_to_sequence(red_edges)

    for perm_dimensions in itertools.permutations(range(n)):
        for flip_dimensions in itertools.product([0, 1], repeat=n):

            def permute_and_flip(v):
                # print(f"Permuting {v} with {perm_dimensions} and flipping {flip_dimensions}")
                return tuple((v[perm_dimensions[i]] if flip_dimensions[i] == 0 else 1 - v[perm_dimensions[i]] for i in range(n)))

            permuted_edges = [(permute_and_flip(u), permute_and_flip(v)) for u, v in red_edges]
            permuted_edges_seq = edges_to_sequence(permuted_edges)

            if permuted_edges_seq < original_edges_seq:
                return False

            if plusNegated:
                if [(1 - i) for i in permuted_edges_seq] < original_edges_seq:
                    return False
    return True
