
peak_counts = {3: range(1, 6+1),
               4: range(1, 24+1),
               5: range(1, 80+1)}

for dimension in [3, 4, 5]:
    for nb_peaks in range(0, 2**(dimension-1)+1):
        for prop in ["RSE", "SE"]:
            for edim in range(1, dimension):
                filename = f"data/peaks-to-{prop}-"
                filename += f"dimension{dimension}-"
                filename += f"edim{edim}-"
                filename += f"peaks{nb_peaks}.param"
                with open(filename, "w", encoding="utf8") as f:
                    print(f"""
                    letting dimension be {dimension}
                    letting nb_peaks be {nb_peaks}
                    letting props be
                    {{
                        ({edim}, 1, {prop}, -1)
                    }}
                    """, file=f)
                for peak_count in peak_counts[dimension]:
                    filename = f"data/peaks-to-{prop}-"
                    filename += f"dimension{dimension}-"
                    filename += f"edim{edim}-"
                    filename += f"peaks{nb_peaks}-"
                    filename += f"count{peak_count}.param"
                    with open(filename, "w", encoding="utf8") as f:
                        print(f"""
                        letting dimension be {dimension}
                        letting nb_peaks be {nb_peaks}
                        letting props be
                        {{
                            ({edim}, 1, {prop}, {peak_count})
                        }}
                        """, file=f)
