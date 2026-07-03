import optimisation as op

import argparse

def main(date):
    print("Date :", date)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("date", help="Date au format jj/mm/aaaa")

    args = parser.parse_args()

    main(args.date)

    day = str(args.date)

    D = op.initialize_data("Partie_1_LLM/data/Export_Planning_du_12_01_2026_au_16_01_2026.xlsx", f"Partie_1_LLM/data/Services_Agents_non_affectés_le_{day.replace("/","_")}.xlsx", day)
    W = op.W_initialize("Partie_2_Optimisation/preferences_agents.xlsx", f"Partie_1_LLM/data/Services_Agents_non_affectés_le_{day.replace("/","_")}.xlsx", (len(D), len(D[0])), D)

    mat_res = op.opti(W,D)

    op.update_planning(mat_res,day)
    dico_mach = op.create_dico_affectés(mat_res,day)
    liste_serv = op.create_liste_non_affecté(mat_res, day)





