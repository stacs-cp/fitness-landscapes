from pathlib import Path


face_counts = {3: range(0, 6+1),
               4: range(0, 24+1),
               5: range(0, 80+1)}

def dimension_parampart(dimension):
    return Path(f"intermediate-data/dimension-{dimension}.parampart").read_text(encoding="utf8")


for dimension in [3, 4, 5]:
    parampart = dimension_parampart(dimension)
    for nb_peaks in range(1, 2**(dimension-1)+1):
        for prop in ["RSE", "SE"]:
#            for edim in [1,2]:
                # filename = f"data/peaks-to-{prop}-"
                # filename += f"dimension{dimension}-"
                # filename += f"edim{edim}-"
                # filename += f"peaks{nb_peaks}.param"
                # with open(filename, "w", encoding="utf8") as f:
                #     print(f"""
                #     letting dimension be {dimension}
                #     letting nb_peaks be {nb_peaks}
                #     letting props be
                #     {{
                #         ({edim}, 1, {prop}, -1)
                #     }}
                #     """, file=f)
            for peak_count in face_counts[dimension]:
                filename = f"input/peaks-to-{prop}-"
                filename += f"dimension-{dimension}-"
#                filename += f"edim-{edim}-"
                filename += f"peaks-{nb_peaks}-"
                filename += f"count-{peak_count}.param"
                with open(filename, "w", encoding="utf8") as f:
                    f.write(
                        "\n".join(
                            [
                                f"letting dimension be {dimension}",
                                f"letting nb_peaks be {nb_peaks}",
                                "letting props be",
                                "{",
                                f"    (1, 1, {prop}, {peak_count})",
                                "}",
                                "",
                                parampart,
                            ]
                        )
                    )
