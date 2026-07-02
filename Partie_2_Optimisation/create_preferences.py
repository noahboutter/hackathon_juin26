import sys
import re
import random
import pandas as pd


CHEMIN_FICHIER_SOURCE = "../Partie_1_LLM/data/Export_Planning_du_12_01_2026_au_16_01_2026.xlsx"
CHEMIN_FICHIER_SORTIE = "preferences_agents.xlsx"

COLONNE_QUALIFICATION = "qualification"


def melanger_liste(liste):
    """
    Renvoie une copie mélangée de la liste donnée.
    """
    copie = liste.copy()
    random.shuffle(copie)
    return copie


def main():
    if len(sys.argv) != 2:
        print("Utilisation : python create_preferences.py n")
        sys.exit(1)

    n = int(sys.argv[1])

    df = pd.read_excel(CHEMIN_FICHIER_SOURCE)

    df["qualification"] = df["Qualification : Connaissance de ligne"].apply(
        lambda y: [int(x) for x in re.findall(r"\d+", str(y))] if pd.notna(y) else []
    )

    if COLONNE_QUALIFICATION not in df.columns:
        raise ValueError(f"La colonne '{COLONNE_QUALIFICATION}' est absente du fichier source.")

    if n > len(df):
        raise ValueError(
            f"n = {n}, mais le fichier source ne contient que {len(df)} lignes."
        )

    preferences_ligne = []
    preferences_horaire = []

    horaires_possibles = ["AM", "NUIT", "MAT", "JOUR", "COUP"]

    for i in range(n):
        qualification = df[COLONNE_QUALIFICATION].iloc[i]

        qualification_melangee = melanger_liste(qualification)
        horaire_melange = melanger_liste(horaires_possibles)

        preferences_ligne.append(", ".join(map(str, qualification_melangee)))
        preferences_horaire.append(", ".join(horaire_melange))

    df_sortie = pd.DataFrame({
        "identifiant": list(range(1, n + 1)),
        "préférence_ligne": preferences_ligne,
        "préférence_horaire": preferences_horaire
    })

    df_sortie.to_excel(CHEMIN_FICHIER_SORTIE, index=False)

    print(f"Fichier créé : {CHEMIN_FICHIER_SORTIE}")


if __name__ == "__main__":
    main()