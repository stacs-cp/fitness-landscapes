
for dimension in [3,4,5]:
    for nb_peaks in range(1, 2**(dimension-1)):
        for prop in ["RSE", "SE"]:
            with open(f"data/peaks-to-{prop}-dimension{dimension}-peaks{nb_peaks}.param", "w", encoding="utf8") as f:
                print(f"""
                $ Relation of peaks to higher dimension RSE
                $ (this needs automating over the range of peaks [1..2**(dimension-1)])
                $ we need that phase transition/almond shaped table.
                letting dimension be {dimension}
                letting nb_peaks be {nb_peaks}
                letting props be
                {{
                    (2, 1, {prop}, -1)
                }}
                """, file=f)
