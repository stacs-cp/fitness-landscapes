import sys, json

with open(sys.argv[1], "r") as f:
    solutions = json.load(f)
    for solution in solutions:
        edgeset = []
        direction = solution["direction"]
#        print(direction)
        for n1, x1 in enumerate(direction):
            for n2, x2 in enumerate(x1):
                for n3, x3 in enumerate(x2):
                    for n4, x4 in enumerate(x3):
                        for n5, x5 in enumerate(x4):
                            for n6, x6 in enumerate(x5):
                                if x6:
                                    node1 = n1 * 4 + n2 * 2 + n3
                                    node2 = n4 * 4 + n5 * 2 + n6
                                    edgeset.append([node1, node2])
                                    # print(n1, n2, n3, n4, n5, n6, x6)

        # for e in edgeset:
        #     e[0] = format(e[0]-1, '03b')
        #     e[1] = format(e[1]-1, '03b')
        print(sorted(edgeset),"\n")



